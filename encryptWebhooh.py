from cryptography.fernet import Fernet
import sys

key = Fernet.generate_key()
f = Fernet(key)

def encryptString(stringToEncrypt):    
    encryptedString = f.encrypt(stringToEncrypt.encode("utf-8"))
    return encryptedString, key

# take one argument passed from terminal, return encrypted string and key
def main():
    stringToEncrypt = sys.argv[1]
    encryptedString, key = encryptString(stringToEncrypt)
    decryptedString = f.decrypt(encryptedString).decode("utf-8")
    print("Encrypted String: " + str(encryptedString))
    print("Key:              " + str(key))
    print("Decrypted String: " + decryptedString)

if __name__ == "__main__":
    main()