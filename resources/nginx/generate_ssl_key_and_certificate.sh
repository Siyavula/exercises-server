#!/bin/sh

echo
echo "We're about to generate a self-signed SSL certificate and key pair."
echo
echo " * You have to provide a password for this process to work since"
echo "   openssl requires it."
echo " * You have to enter the same password 3 times."
echo " * This password will not be needed again once we're done."

openssl genrsa -des3 -out server.key.secure 2048
openssl rsa -in server.key.secure -out server.key.insecure
mv server.key.insecure server.key
rm server.key.secure
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
rm server.csr
