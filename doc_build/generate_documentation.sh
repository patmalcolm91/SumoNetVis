# Script to re-build documentation and place in proper folders for GitHub

make html;

rm -rf ../docs/*

mv -f _build/doctrees/* ../docs/.doctrees/;
rmdir _build/doctrees;

mv -f _build/html/* ../docs/;
rm _build/html/.buildinfo
rmdir _build/html;

rmdir _build
