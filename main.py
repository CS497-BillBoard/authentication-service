import ssl

def main():
    print("Hello World")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain('cert.pem', 'private.pem')

main()