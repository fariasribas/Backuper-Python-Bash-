#!/usr/bin/env python3
import tarfile
import os
import shutil
import subprocess

# Nomes fixos dos arquivos de configuração
CONFIG_FILE = "backup.conf"
DESTINOS_FILE = "destinos.conf"
PASS_FILE = "pass.conf"

# Função para ler arquivos e pastas de um arquivo de configuração
def read_config_file(config_file):
    files_folders = []
    try:
        with open(config_file, 'r') as file:
            for line in file:
                path = line.strip()
                if os.path.isfile(path) or os.path.isdir(path):
                    files_folders.append(path)
    except Exception as e:
        print(f"Erro ao ler o arquivo de configuração: {e}")
    return files_folders

# Função para ler destinos de backup de um arquivo de configuração
def read_destinations_file(dest_file):
    destinations = []
    try:
        with open(dest_file, 'r') as file:
            for line in file:
                path = line.strip()
                if os.path.isdir(os.path.dirname(path)) or not os.path.exists(path):
                    destinations.append(path)
    except Exception as e:
        print(f"Erro ao ler o arquivo de destinos: {e}")
    return destinations

# Função para ler a senha do arquivo pass.conf
def read_password_file(pass_file):
    if os.path.isfile(pass_file):
        try:
            with open(pass_file, 'r') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Erro ao ler o arquivo de senha: {e}")
    else:
        print(f"Arquivo de senha não encontrado: {pass_file}")
    return None

# Função para adicionar todos os arquivos de uma pasta
def get_files_from_directory(directory):
    file_list = []
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_list.append(os.path.join(root, file))
    except Exception as e:
        print(f"Erro ao listar arquivos do diretório {directory}: {e}")
    return file_list

# Função para criar um arquivo de backup compactado
def create_backup(files_folders, backup_name):
    try:
        with tarfile.open(backup_name, "w:gz") as tar:
            for path in files_folders:
                if os.path.isfile(path):
                    tar.add(path, arcname=os.path.relpath(path, start=os.path.commonpath(files_folders)))
                elif os.path.isdir(path):
                    for file in get_files_from_directory(path):
                        tar.add(file, arcname=os.path.relpath(file, start=os.path.commonpath(files_folders)))
    except Exception as e:
        print(f"Erro durante a criação do backup: {e}")

# Função para criptografar o backup usando GPG
def encrypt_backup(backup_name, password):
    encrypted_backup_name = backup_name + ".gpg"
    try:
        command = f'gpg --batch --yes --passphrase "{password}" --symmetric --cipher-algo AES256 {backup_name}'
        subprocess.run(command, shell=True, check=True)
        os.rename(backup_name + '.gpg', encrypted_backup_name)
        os.remove(backup_name)
        return encrypted_backup_name
    except subprocess.CalledProcessError as e:
        print(f"Erro durante a criptografia do backup: {e}")
    except Exception as e:
        print(f"Erro ao renomear ou remover arquivo: {e}")
    return None

# Função para gerenciar e renomear backups antigos
def manage_old_backups(encrypted_backup_name, destinations):
    try:
        for destination in destinations:
            backup_base = os.path.join(destination, os.path.basename(CONFIG_FILE).replace('.conf', ''))
            backup_path = backup_base + ".gpg"
            backup_old_path = backup_base + "_old.gpg"
            backup_very_old_path = backup_base + "_very_old.gpg"
            
            if os.path.exists(backup_path):
                if os.path.exists(backup_old_path):
                    if os.path.exists(backup_very_old_path):
                        os.remove(backup_very_old_path)
                    shutil.move(backup_old_path, backup_very_old_path)
                shutil.move(backup_path, backup_old_path)

            shutil.copy2(encrypted_backup_name, backup_path)
            
    except Exception as e:
        print(f"Erro ao gerenciar ou copiar backups antigos: {e}")

# Função principal para processar arquivos de configuração e criar backups em múltiplos locais
def main():
    try:
        if not os.path.isfile(CONFIG_FILE):
            print(f"Arquivo de configuração não encontrado: {CONFIG_FILE}")
            return
        
        if not os.path.isfile(DESTINOS_FILE):
            print(f"Arquivo de destinos não encontrado: {DESTINOS_FILE}")
            return

        if not os.path.isfile(PASS_FILE):
            print(f"Arquivo de senha não encontrado: {PASS_FILE}")
            return
        
        files_folders = read_config_file(CONFIG_FILE)
        destinations = read_destinations_file(DESTINOS_FILE)
        password = read_password_file(PASS_FILE)
        
        if files_folders and destinations and password:
            backup_name = os.path.basename(CONFIG_FILE).replace('.conf', '.tar.gz')
            create_backup(files_folders, backup_name)
            encrypted_backup_name = encrypt_backup(backup_name, password)
            if encrypted_backup_name:
                manage_old_backups(encrypted_backup_name, destinations)
        else:
            print("Nenhum arquivo ou pasta válido encontrado no arquivo de configuração ou destinos.")
    
    except Exception as e:
        print(f"Erro durante a execução do backup: {e}")

if __name__ == "__main__":
    main()
