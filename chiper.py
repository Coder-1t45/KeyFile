
from random import randint
MAX = 65535

#   *INDEX*
def indexE(plain: str, mp:int=1) -> str:
    encrypted = ""
    for i in range(len(plain)):
        encrypted += chr((ord(plain[i]) + i*mp) % MAX)
    return encrypted

def indexD(plain: str,  mp:int=1) -> str:
    decrypted = ""
    for i in range(len(plain)):
        decrypted += chr((ord(plain[i]) - i*mp) % MAX)
    return decrypted
#   *CEASAR*
def ceasarE(plain:str, k:int) -> str:
    encrypted=""
    for letter in plain:
        encrypted += chr((ord(letter) + k) % MAX)
    return encrypted

def ceasarD(plain:str, k:int) -> str:
    encrypted=""
    for letter in plain:
        encrypted += chr((ord(letter) - k) % MAX)
    return encrypted

#   *MODULO*
def moduleE(plain:str, k:int) -> str:
    encrypted=""
    for letter in plain:
        encrypted += chr((ord(letter) * k)%MAX)
    return encrypted
def moduleD(plain:str, k:int) -> str:
    decrypted=""
    for letter in plain:
        decrypted += chr(
            (
                ord(letter) + MAX * (ord(letter) % k)
                )//k
            )
    return decrypted
#   *CEASAR*

def appE(plain:str, pk: int):
    encrypted = plain
    for d in str(pk):
        digit = int(d)
        encrypted = indexE (encrypted, (digit % 5) +1)
    return encrypted