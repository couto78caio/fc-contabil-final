from Crypto.Cipher import AES
import os

# AVISO: O modo AES.MODE_ECB não é recomendado para a maioria das aplicações
# pois não fornece confidencialidade semântica. Considere usar AES.MODE_CBC ou AES.MODE_GCM
# com um vetor de inicialização (IV) único para cada criptografia, se a segurança
# dos dados em repouso for crítica e se houver necessidade de descriptografia.

AES_KEY_ENV = os.getenv("AES_KEY")

if not AES_KEY_ENV:
    raise ValueError("A variável de ambiente AES_KEY não está definida. Esta chave é essencial para a criptografia dos arquivos.")

KEY = AES_KEY_ENV.encode()

if len(KEY) not in (16, 24, 32):
    raise ValueError(f"A AES_KEY deve ter 16, 24 ou 32 bytes. O tamanho atual é {len(KEY)} bytes. Verifique a variável de ambiente AES_KEY.")

def pad(data: bytes) -> bytes:
    """Preenche dados para múltiplo de 16 bytes (tamanho do bloco AES)."""
    return data + b"\0" * (AES.block_size - len(data) % AES.block_size)

def encrypt_file(filepath: str):
    """Criptografa o arquivo no próprio lugar usando AES-ECB com a chave definida em AES_KEY."""
    try:
        with open(filepath, "rb") as f:
            data = f.read()

        cipher = AES.new(KEY, AES.MODE_ECB)
        encrypted_data = cipher.encrypt(pad(data))

        with open(filepath, "wb") as f:
            f.write(encrypted_data)
        # print(f"Arquivo {filepath} criptografado com sucesso.") # Log para debug, remover em produção

    except FileNotFoundError:
        # print(f"Erro: Arquivo {filepath} não encontrado para criptografia.") # Log para debug
        raise # Re-levanta a exceção para ser tratada no chamador
    except Exception as e:
        # print(f"Erro ao criptografar o arquivo {filepath}: {e}") # Log para debug
        raise # Re-levanta a exceção

# Se a descriptografia for necessária, uma função como esta seria implementada:
# def decrypt_file(filepath: str, key: bytes = KEY):
#     """Descriptografa o arquivo no próprio lugar usando AES-ECB."""
#     with open(filepath, "rb") as f:
#         encrypted_data = f.read()
# 
#     cipher = AES.new(key, AES.MODE_ECB)
#     decrypted_data_padded = cipher.decrypt(encrypted_data)
#     
#     # Remove o padding (assumindo padding com \0)
#     decrypted_data = decrypted_data_padded.rstrip(b"\0")
# 
#     with open(filepath, "wb") as f:
#         f.write(decrypted_data)

