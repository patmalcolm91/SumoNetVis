# Script to re-build documentation and place in proper folders for GitHub

make html;

mv doctrees/* ../docs/.doctrees;
rmdir doctrees;

mv html/* ../docs;
rmdir html;
