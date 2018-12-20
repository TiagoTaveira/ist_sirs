#!/usr/bin/env bash


echo "Creating certificates..."

echo "What name do you want to give to the ROOT certificate?"
read rootCertificate

echo "What name do you want to give to the SERVER certificate?"
read serverCertificate

echo "What name do you want to give to the KDC certificate?"
read kdcCertificate

Key = "Key"

# generate certificate for main Server

openssl req -x509 -newkey rsa:2048 -keyout $rootCertificate$Key.pem -out $rootCertificate.pem -days 365

openssl req -out $serverCertificate.csr -new -newkey rsa:2048 -nodes -keyout $serverCertificate.key

openssl req -verify -in $serverCertificate.csr -text -noout

openssl x509 -req -days 360 -in $serverCertificate.csr -CA $rootCertificate.pem -CAkey $rootCertificate$Key.pem -CAcreateserial -out $serverCertificate.crt -sha256

openssl x509 -text -noout -in $serverCertificate.crt

# generate certificate for KDC

openssl req -out $kdcCertificate.csr -new -newkey rsa:2048 -nodes -keyout $kdcCertificate.key

openssl req -verify -in $kdcCertificate.csr -text -noout

openssl x509 -req -days 360 -in $kdcCertificate.csr -CA $rootCertificate.pem -CAkey $rootCertificate$Key.pem -CAcreateserial -out $kdcCertificate.crt -sha256

openssl x509 -text -noout -in $kdcCertificate.crt

mkdir $rootCertificate
mkdir $serverCertificate
mkdir $kdcCertificate

mv $rootCertificate.* ./$rootCertificate
mv $serverCertificate.* ./$serverCertificate
mv $kdcCertificate.* ./$kdcCertificate

echo "Certificates generated successfuly."
echo "Exiting the program..."
