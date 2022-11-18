#import threading
import os
from os import path
import sys

import json
import chiper
import rsa

import shutil
import tkinter.messagebox as tkm
import winreg as reg
import tkinter as tk
#format handeling
__format = '.locked'
__directory_format = 'directory'
__rsa_nb = 1024
__ceasar_key = 125

def get_format(path: str):
    return path.split('.')[-1]
def dirList(_dir:str):
    files:list[str] = []
    dirs:list[str] = []
    for file in os.listdir(_dir):
        if path.isdir(path.join(_dir, file)):
            dirs.append(path.join(_dir,file))
            expected = dirList(path.join(_dir, file))
            files += expected[0]
            dirs += expected[1]
        else:
            files.append(path.join(_dir, file))
    return [i.replace('\\','/') for i in files], [i.replace('\\','/') for i in dirs] 

#bytes handeling
def b_fromBytes(inp:bytes)->str:
    return repr(inp)[2:-1]
def b_toBytes(inp:str)->bytes:
    return eval(rf"""b'{inp}'""")

def collectPrivate(string:str)->rsa.PrivateKey:
    d =  string.replace(' ','').replace('PrivateKey(','').replace(')','').split(',')
    n,e,d,p,q = tuple(map(int,d))
    return rsa.PrivateKey(n,e,d,p,q)

#file system
def fileLock(_path,_password:str):
    _old_format = get_format(_path)
    _file_reader = open(_path, 'rb')

    [pk, rk] = rsa.newkeys(__rsa_nb)
    _data:dict = {
        'password': b_fromBytes( rsa.encrypt((_password.encode('utf-16')),pk)),
        'format': _old_format,
        'key': chiper.indexE( str(rk)),
        'inside': b_fromBytes(_file_reader.read())
    }
    _file_reader.close()
    _file_writer = open(_path, 'wb')

    str_data:str = json.dumps(_data)
    _file_writer.write(bytearray(chiper.ceasarE(str_data,__ceasar_key), encoding='utf-16'))

    _file_writer.close()

    os.rename(_path, _path[0:-1-len(_old_format)]+__format)

    return 1
def fast_read(_path):
    f = open(_path, 'rb')
    v = f.read()
    f.close()
    return v

#directory system
def dirLock(_path, _password:str):
    _old_format = __directory_format
    [pk, rk] = rsa.newkeys(__rsa_nb) 
    _content_files, _content_dirs = dirList(_path)
    _data:dict = {
        'password': b_fromBytes( rsa.encrypt((_password.encode('utf-16')),pk)),
        'format': _old_format,
        'key': chiper.indexE( str(rk)),
        'inside': {'folder':_content_dirs,
            'files':{_miny_file: b_fromBytes(fast_read(_miny_file)) for _miny_file in _content_files}
        }
    }
    _file_writer = open(_path+__format, 'wb')

    str_data:str = json.dumps(_data)
    _file_writer.write(bytearray(chiper.ceasarE(str_data,__ceasar_key), encoding='utf-16'))
    _file_writer.close()

    #delete folder
    shutil.rmtree(_path)
    return 1
def unlock(_path,input_password:str):
    _file_reader =open(_path, 'rb')
    _data = json.loads(chiper.ceasarD(_file_reader.read().decode('utf-16'),__ceasar_key))
    _file_reader.close()

    _format:str = _data['format']
    _key:rsa.PrivateKey = collectPrivate(chiper.indexD(_data['key']))
    _password:str = rsa.decrypt((b_toBytes(_data['password'])),_key).decode('utf-16')

    #ask for aproval to continue
    if input_password != _password: return -1

    if _format != __directory_format:
        _inside:bytes = b_toBytes( _data['inside'])
        _file_writer = open(_path,'wb')
        _file_writer.write(_inside)
        _file_writer.close()

        os.rename(_path, _path[0:-len(get_format(_path))]+_format)
    else:
        _inside:str =_data['inside']
        for i in _inside['folder'] + [_path.replace(__format,'')]:
            try: 
                os.makedirs(i)
            except FileExistsError:
                continue
        _files:dict = _inside['files']
        for file_path, file_inside in _files.items():
            open(file_path,'x').close()
            with open(file_path, 'wb') as f:
                f.write(b_toBytes(file_inside))
        os.remove(_path)
    return 1

#switching system
def main(_path, _password):
    if path.isfile(_path):
        if get_format(_path) in __format:
            print('unlock')
            return unlock(_path,_password)
        else:
            print('fileLock')
            return fileLock(_path,_password)
    else:
        print('dirLock')
        return dirLock(_path,_password)


def request_password(f = None):
    root= tk.Tk()

    tk.Label(root,text="Password:",font=('Arial',15), anchor="nw").place(relwidth=0.23, relx=0.01)
    entry1 = tk.Entry(root, font=('Arial',15))
    def oninput():
        _password = entry1.get()
        entry1.destroy()
        tk.Label(root,text="This can take a while...",font=('Arial',15), anchor="nw").place(relx=0.25, relwidth=0.73)
        if (f != None): f(_password)
        root.destroy()
        root.quit()
    entry1.bind("<Return>", lambda x:oninput())
    entry1.place(relx=0.25, relwidth=0.73)

    root.title("KeyFile")
    root.geometry('450x40')

    root.mainloop()

#https://youtu.be/tQJ1R-jafSw
#https://stephen-edwards-27564.medium.com/adding-python-scripts-to-the-right-click-menu-context-menu-of-windows-6bf83ece5c47


# Get path of current working directory and python.exe
cwd = os.getcwd()
python_exe = sys.executable

__aplication_name = 'keyfile.exe'
# optional hide python terminal in windows
hidden_terminal = '\\'.join(python_exe.split('\\')[:-1]) + "\\pythonw.exe"

# Set the path of the context menu (right-click menu)
key_path = r'*\\shell\\KeyFile'
directory_key_path = r'Directory\\shell\\KeyFile'

# Create outer key

def uninstall():
    reg.DeleteKey(reg.HKEY_CLASSES_ROOT, key_path+r'\\command')
    reg.DeleteKey(reg.HKEY_CLASSES_ROOT, directory_key_path+r'\\command')
    reg.DeleteKey(reg.HKEY_CLASSES_ROOT, key_path)
    reg.DeleteKey(reg.HKEY_CLASSES_ROOT, directory_key_path)

def install():
    def installKey(_path):
        # if Outer key does not exist create it
        key = reg.CreateKey(reg.HKEY_CLASSES_ROOT, _path)

        # Change 'Organise folder' to the function of your script
        reg.SetValue(key, '', reg.REG_SZ, '&KeyFile this')

        # create inner key
        key1 = reg.CreateKey(key, r"command")

        # change 'file_organiser.py' to the name of your script
        reg.SetValue(key1, '', reg.REG_SZ,
                    python_exe + f' "{cwd}\\{__aplication_name}" "%1"')
        #print("key successfully created.")
        # reg.SetValue(key1, '', reg.REG_SZ, hidden_terminal + f' "{cwd}\\file_organiser.py"')  # use to to hide terminal
    
    try:
        # Check if outer key exists
        key = reg.OpenKey(reg.HKEY_CLASSES_ROOT, key_path)
        uninstall()
        tkm.showinfo('KeyFile','program is uninstalled')

    except FileNotFoundError:
        installKey(key_path)
        installKey(directory_key_path)
        tkm.showinfo('KeyFile','program is installed')


if __name__ == '__main__':
    try:
        if (len(sys.argv) == 3):
            _path = sys.argv[2]
        else:
            _path = sys.argv[1]
        def gathered(_password):
            #main(_path,_password)
            print(f'gathered password "{_password}"')
            code = main(_path,_password)
            tkm.showinfo('KeyFile',f'program has finished with code {code}')

        request_password(f=gathered)
    except IndexError:
        install()
    except Exception as e:
        tkm.showerror('KeyFile',e)

#pyinstaller --onefile --noconsole --icon=icon.ico  keyfile.py