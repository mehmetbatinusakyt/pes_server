import os
from OpenSSL import crypto
from datetime import datetime, timedelta

def create_self_signed_cert():
    # Create certs directory if it doesn't exist
    if not os.path.exists('certs'):
        os.makedirs('certs')

    # Generate key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().C = "BG"
    cert.get_subject().ST = "Sofia"
    cert.get_subject().L = "Sofia"
    cert.get_subject().O = "PES Server"
    cert.get_subject().OU = "Development"
    cert.get_subject().CN = "localhost"

    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    # Save private key
    with open("certs/private.key", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    # Save certificate
    with open("certs/certificate.crt", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

if __name__ == "__main__":
    create_self_signed_cert()
    print("Certificate and private key have been generated in 'certs' directory.")