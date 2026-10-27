#!/usr/bin/env python3

import argparse
import hashlib
import json
from collections import Counter, defaultdict
import math
from pathlib import Path
import statistics
import sys


def xyz(value):
    return tuple(float(getattr(value, axis)) for axis in ("x", "y", "z"))


def finite(values):
    return all(math.isfinite(value) for value in values)


def angles(vector):
    x, y, z = vector
    return math.atan2(math.hypot(x, y), z), math.atan2(y, x)


def wrap_phi(value):
    return math.atan2(math.sin(value), math.cos(value))


def opening_angle(left, right):
    a, b = math.hypot(*left), math.hypot(*right)
    if a == 0 or b == 0:
        return math.inf
    cross = (left[1]*right[2] - left[2]*right[1],
             left[2]*right[0] - left[0]*right[2],
             left[0]*right[1] - left[1]*right[0])
    return math.atan2(math.hypot(*cross), sum(x*y for x, y in zip(left, right)))


def covariance_ok(matrix):
    n = len(matrix)
    scale = max(abs(x) for row in matrix for x in row)
    if scale == 0:
        return True
    a = [[x / scale for x in row] for row in matrix]
    tolerance = 2e-6
    if any(a[i][i] < -tolerance for i in range(n)):
        return False
    for i in range(n):
        for j in range(i):
            if a[i][i]*a[j][j] - a[i][j]**2 < -tolerance:
                return False
    if n == 3:
        determinant = (a[0][0]*(a[1][1]*a[2][2] - a[1][2]**2)
                       - a[0][1]*(a[0][1]*a[2][2] - a[1][2]*a[0][2])
                       + a[0][2]*(a[0][1]*a[1][2] - a[1][1]*a[0][2]))
        return determinant >= -tolerance
    return True


def read_cluster(cluster):
    position = xyz(cluster.getPosition())
    direction_error = xyz(cluster.getDirectionError())
    packed = [float(v) for v in cluster.getPositionError().values]
    if len(packed) != 6:
        raise RuntimeError("Expected six packed position covariance entries")
    xx, xy, yy, xz, yz, zz = packed
    covariance = ((xx, xy, xz), (xy, yy, yz), (xz, yz, zz))
    data = {
        "energy": float(cluster.getEnergy()),
        "energy_error": float(cluster.getEnergyError()),
        "theta": float(cluster.getITheta()),
        "phi": float(cluster.getIPhi()),
        "position": position,
        "direction_error": direction_error,
        "covariance": covariance,
    }
    values = [data[k] for k in ("energy", "energy_error", "theta", "phi")]
    if not finite(values + list(position) + list(direction_error) + packed):
        raise ValueError("non-finite photon field")
    if data["energy"] < 0 or data["energy_error"] < 0:
        raise ValueError("negative energy or energy error")
    vp, cp, vt = direction_error
    if not covariance_ok(((vp, cp), (cp, vt))) or not covariance_ok(covariance):
        raise ValueError("invalid photon covariance (not positive semidefinite)")
    if not 0 <= data["theta"] <= math.pi + 1e-6:
        raise ValueError("pointing theta outside [0, pi]")
    data["pointing"] = vp > 0 and vt > 0
    data["position_error"] = xx > 0 or yy > 0 or zz > 0
    data["complete"] = (data["pointing"] and data["position_error"]
                        and data["energy_error"] > 0)
    data["all_zero"] = (data["energy_error"] == 0
                        and not any(direction_error) and not any(packed))
    return data


def impact_sigmas(direction, covariance):
    x, y, z = direction
    rt = math.hypot(x, y)
    r2 = x*x + y*y + z*z
    if rt == 0 or r2 == 0:
        return None
    gradients = ((x*z/(r2*rt), y*z/(r2*rt), -rt/r2),
                 (-y/(rt*rt), x/(rt*rt), 0))
    variances = [sum(g[i]*covariance[i][j]*g[j]
                     for i in range(3) for j in range(3)) for g in gradients]
    if min(variances) <= 0:
        return None
    return tuple(math.sqrt(v) for v in variances)


def describe(values):
    if not values:
        return "N=0"
    ordered = sorted(values)
    median = statistics.median(ordered)
    width = statistics.stdev(values) if len(values) > 1 else 0.0
    return (f"N={len(values)}, mean={statistics.mean(values):+.6g}, "
            f"std={width:.6g}, median={median:+.6g}, "
            f"min={ordered[0]:+.6g}, max={ordered[-1]:+.6g}")



def known_zero_position_covariance(cluster):
    position = xyz(cluster.getPosition())
    errors = xyz(cluster.getDirectionError())
    covariance = [float(v) for v in cluster.getPositionError().values]
    energy = float(cluster.getEnergy())
    energy_error = float(cluster.getEnergyError())
    theta, phi = float(cluster.getITheta()), float(cluster.getIPhi())
    ordinary = position + errors + (energy, energy_error, theta, phi)
    return (finite(ordinary) and 0 < energy < 0.010 and energy_error > 0
            and all(v == 0 for v in position + errors + (theta, phi))
            and len(covariance) == 6 and all(math.isnan(v) for v in covariance))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--signal-tau-pdg", type=int, choices=(15, -15), required=True)
    parser.add_argument("--expected-events", type=int, required=True)
    parser.add_argument("--cone-mrad", type=float, default=10.0)
    parser.add_argument("--vertex-sigmas-mm", type=float, nargs=3,
                        default=(5.96e-3, 23.8e-6, 0.397))
    parser.add_argument("--allow-known-zero-position-covariance", action="store_true")
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()
    if args.expected_events < 1 or not math.isfinite(args.cone_mrad) or args.cone_mrad <= 0:
        parser.error("Event count and matching cone must be positive")
    if not finite(args.vertex_sigmas_mm) or min(args.vertex_sigmas_mm) <= 0:
        parser.error("Vertex sigmas must be finite and positive")

    from podio.reading import get_reader

    print("File:", args.file.resolve())
    print("Python:", sys.executable)
    print("Signal tau PDG:", args.signal_tau_pdg)
    print("Matching: exactly one cluster within", args.cone_mrad,
          "mrad of truth photon flight direction; no energy selection")
    print("Statistics are unweighted and conditional on this geometric selection.")
    print("Known-case policy enabled:", args.allow_known_zero_position_covariance)
    print("All ROOT data remain unchanged. Known invalid clusters are excluded from diagnostics only.")
    counts = Counter()
    failures = Counter()
    details = []
    known_issues = []
    values = defaultdict(list)
    vertices = []
    energy_bins = defaultdict(list)

    def fail(kind, event_number, message):
        failures[kind] += 1
        if len(details) < 12:
            details.append(f"Event {event_number}: {kind}: {message}")

    reader = get_reader(str(args.file))
    muon_pdg = 13 if args.signal_tau_pdg == 15 else -13
    tag_neutrino = -16 if args.signal_tau_pdg == 15 else 16
    for number, event in enumerate(reader.get("events")):
        counts["events"] += 1
        particles = list(event.get("GenParticles"))
        taus = [p for p in particles if abs(int(p.getPDG())) == 15]
        signal = [p for p in taus if int(p.getPDG()) == args.signal_tau_pdg]
        tag = [p for p in taus if int(p.getPDG()) == -args.signal_tau_pdg]
        clusters = []
        for index, raw_cluster in enumerate(event.get("EFlowPhoton")):
            counts["clusters"] += 1
            if (args.allow_known_zero_position_covariance
                    and known_zero_position_covariance(raw_cluster)):
                issue = {"event_index": number, "cluster_index": index,
                         "energy_GeV": float(raw_cluster.getEnergy()),
                         "reason": "zero_position_all_nan_covariance_below_10MeV"}
                known_issues.append(issue)
                counts["known invalid clusters excluded from diagnostics"] += 1
                print("KNOWN ISSUE:", json.dumps(issue, sort_keys=True))
                continue
            try:
                c = read_cluster(raw_cluster)
                if math.hypot(*c["position"]) == 0:
                    raise ValueError("zero cluster impact position")
            except ValueError as exc:
                fail("invalid cluster", number, f"cluster {index}: {exc}")
                continue
            clusters.append((index, c))
            counts["clusters with complete uncertainties"] += int(c["complete"])
            counts["clusters with all-zero uncertainties"] += int(c["all_zero"])
            counts["clusters with partial uncertainties"] += int(not c["complete"] and not c["all_zero"])

        if len(signal) != 1 or len(tag) != 1:
            fail("tau multiplicity", number, f"signal={len(signal)}, tag={len(tag)}")
            continue
        origin, other_origin = xyz(signal[0].getVertex()), xyz(tag[0].getVertex())
        if not finite(origin + other_origin):
            fail("vertex", number, "non-finite coordinates")
        elif max(abs(a-b) for a, b in zip(origin, other_origin)) > 1e-9:
            fail("vertex", number, "tau production vertices differ")
        else:
            vertices.append(origin)
        time = float(signal[0].getTime())
        if not math.isfinite(time):
            fail("time", number, "non-finite stored MC time")
        counts["nonzero signal MC times"] += int(time != 0)

        daughters = list(signal[0].getDaughters())
        pdgs = sorted(int(p.getPDG()) for p in daughters)
        tag_pdgs = [int(p.getPDG()) for p in tag[0].getDaughters()]
        if pdgs != sorted([muon_pdg, 22]) or tag_neutrino not in tag_pdgs:
            fail("LFV truth", number, f"signal daughters={pdgs}, tag daughters={tag_pdgs}")
            continue
        gamma = next(p for p in daughters if int(p.getPDG()) == 22)
        momentum, gamma_origin = xyz(gamma.getMomentum()), xyz(gamma.getVertex())
        photon_energy = math.hypot(*momentum, float(gamma.getMass()))
        parent_mass = float(signal[0].getMass())
        daughter_p4 = [(xyz(p.getMomentum()), float(p.getMass())) for p in daughters]
        if (not finite(momentum + gamma_origin + (photon_energy, parent_mass))
                or not all(finite(p + (m,)) for p, m in daughter_p4)
                or math.hypot(*momentum) == 0):
            fail("LFV truth", number, "non-finite or zero photon kinematics")
            continue
        total_energy = sum(math.hypot(*p, m) for p, m in daughter_p4)
        total_p = tuple(sum(p[i] for p, m in daughter_p4) for i in range(3))
        mass2 = total_energy**2 - sum(x*x for x in total_p)
        if mass2 < 0 or abs(math.sqrt(max(0, mass2)) - parent_mass) > 1e-3:
            fail("LFV mass", number, f"m2={mass2:.9g}, parent mass={parent_mass:.9g}")
        else:
            counts["LFV truth passed"] += 1
            values["truth m(mu,gamma) [GeV]"].append(math.sqrt(mass2))

        near = []
        for index, c in clusters:
            direction = tuple(c["position"][i] - gamma_origin[i] for i in range(3))
            separation = opening_angle(momentum, direction)
            if separation < args.cone_mrad * 1e-3:
                near.append((index, c, direction, separation))
        if not near:
            counts["no cluster within cone"] += 1
            continue
        if len(near) != 1:
            counts["multiple clusters within cone"] += 1
            continue
        index, c, direction, separation = near[0]
        counts["unique geometric match"] += 1
        values["matched separation [mrad]"].append(1000 * separation)
        values["matched Erec/Etruth"].append(c["energy"] / photon_energy)
        if not c["complete"]:
            counts["unique matches with incomplete uncertainties"] += 1
            if counts["unique matches with incomplete uncertainties"] <= 8:
                print(f"REVIEW event {number}, cluster {index}: Etruth={photon_energy:.6g}, "
                      f"Erec={c['energy']:.6g} GeV, complete uncertainty fields absent")
            continue
        counts["unique matches with complete uncertainties"] += 1
        theta_true, phi_true = angles(momentum)
        theta_impact, phi_impact = angles(direction)
        vp, cp, vt = c["direction_error"]
        pulls = {
            "energy pull": (c["energy"] - photon_energy) / c["energy_error"],
            "pointing theta pull": (c["theta"] - theta_true) / math.sqrt(vt),
            "pointing phi pull": wrap_phi(c["phi"] - phi_true) / math.sqrt(vp),
        }
        sigmas = impact_sigmas(direction, c["covariance"])
        if sigmas is not None:
            pulls["impact theta pull"] = (theta_impact - theta_true) / sigmas[0]
            pulls["impact phi pull"] = wrap_phi(phi_impact - phi_true) / sigmas[1]
        else:
            counts["matches without projectable impact errors"] += 1
        for label, value in pulls.items():
            values[label].append(value)
        values["pointing theta residual [mrad]"].append(1000 * (c["theta"] - theta_true))
        values["pointing phi residual [mrad]"].append(1000 * wrap_phi(c["phi"] - phi_true))
        low, high = next((lo, hi) for lo, hi in ((0, 5), (5, 15), (15, 30), (30, math.inf))
                         if lo <= photon_energy < hi)
        energy_bins[(low, high)].append(pulls["energy pull"])

    if counts["events"] != args.expected_events:
        failures["event count"] += 1
    if counts["LFV truth passed"] != counts["events"]:
        failures["not all events passed LFV truth"] += 1
    if counts["unique matches with complete uncertainties"] == 0:
        failures["no signal match with photon uncertainties"] += 1

    print("\nCounts:")
    for label in ("events", "LFV truth passed", "clusters", "clusters with complete uncertainties",
                  "clusters with all-zero uncertainties", "clusters with partial uncertainties",
                  "unique geometric match", "no cluster within cone", "multiple clusters within cone",
                  "unique matches with complete uncertainties", "unique matches with incomplete uncertainties",
                  "matches without projectable impact errors"):
        print(f"  {label}: {counts[label]}")
    print("\nSpatial vertex checks (means assumed zero; sigmas in mm):")
    print("  Shared tau vertices:", len(vertices), "unique:", len(set(vertices)))
    if len(vertices) != counts["events"] or len(set(vertices)) < min(2, counts["events"]):
        failures["vertex completeness or variation"] += 1
    for i, (axis, expected) in enumerate(zip("xyz", args.vertex_sigmas_mm)):
        coordinates = [v[i] for v in vertices]
        if len(coordinates) < 2:
            failures["insufficient vertex data"] += 1
            continue
        mean, width = statistics.mean(coordinates), statistics.stdev(coordinates)
        relative_error = abs(width / expected - 1)
        mean_pull = abs(mean) * math.sqrt(len(coordinates)) / expected
        passed = relative_error <= 0.10 and mean_pull <= 5.0
        verdict = ("PASS" if passed else "FAIL") if len(coordinates) >= 100 else "diagnostic only (N<100)"
        if len(coordinates) >= 100 and not passed:
            failures[f"vertex {axis} distribution"] += 1
        print(f"  {axis}: mean={mean:+.8e}, sigma={width:.8e}, expected={expected:.8e}, "
              f"width difference={relative_error:.2%}, mean pull={mean_pull:.3f}: {verdict}")
    print("  Nonzero signal MC times:", counts["nonzero signal MC times"])
    print("  This checks spatial smearing only; preservation of ct smearing is not certified.")
    print("\nUnweighted diagnostic distributions:")
    for label, sample in values.items():
        print(f"  {label}: {describe(sample)}")
    print("\nEnergy pulls by truth-photon energy (complete, unique matches):")
    for (low, high), sample in sorted(energy_bins.items()):
        print(f"  [{low}, {high}) GeV: {describe(sample)}")
    print("\nGeometric associations may be wrong or merged. Pull means/widths have no automatic pass threshold.")
    print("Unmatched/ambiguous clusters and zero uncertainty fields require interpretation, not forced matching.")
    status = ("failed" if failures else
              "preliminary_pass_with_known_issues" if known_issues else "preliminary_pass")
    print("\nKnown invalid clusters excluded from diagnostics:", len(known_issues))
    if args.json_report:
        digest = hashlib.sha256()
        with args.file.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        report = {
            "schema_version": 1, "status": status,
            "policy": "lfv_preliminary_zero_position_covariance_v1",
            "allow_known_zero_position_covariance": args.allow_known_zero_position_covariance,
            "file": str(args.file.resolve()), "file_sha256": digest.hexdigest(),
            "signal_tau_pdg": args.signal_tau_pdg, "expected_events": args.expected_events,
            "counts": dict(counts), "failures": dict(failures),
            "failure_examples": details, "known_issues": known_issues,
            "limitations": ["unweighted geometric photon associations",
                            "photon-response physics review required",
                            "ct-smearing preservation not certified",
                            "known invalid fields remain in the ROOT file"],
        }
        with args.json_report.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    if failures:
        print("\nPRELIMINARY CHECKS FAILED")
        for label, count in failures.items():
            print(f"  {label}: {count}")
        for detail in details:
            print(" ", detail)
        return 1
    if known_issues:
        print("\nPRELIMINARY CHECKS PASSED WITH KNOWN ISSUES; PHYSICS REVIEW REQUIRED")
    else:
        print("\nPRELIMINARY CHECKS PASSED; PHYSICS REVIEW REQUIRED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"VALIDATOR ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
