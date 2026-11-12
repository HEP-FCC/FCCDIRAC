# Create the proxy for iLCDirac
echo "Initializing the DIRAC/Grid proxy ..."
dirac-proxy-init -g fcc_user
if test "x$?" = "x0" ; then
   echo "Done!"
else
   echo "Some problem occured ..."
fi
