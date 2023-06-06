import yaml
import utils


def read_config(yaml_name):
    """
    Reads a YAML configuration file and returns its contents as a dictionary.

    Args:
        yaml_name (str): The name of the YAML configuration file.

    Returns:
        dict: The contents of the YAML configuration file as a dictionary.

    Raises:
        FileNotFoundError: If the specified YAML configuration file cannot be found.
        TypeError: If the input is not a string.
    """
    try:
        with open(yaml_name, encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Configuration file read error, please check the configuration file name: {yaml_name}")
    except TypeError:
        print("Configuration file read error, please check the input type")


def check_id_rsa_pub(ssh_obj):
    """
    Check if the id_rsa.pub file exists in the /root/.ssh directory.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    cmd = '[ -f /root/.ssh/id_rsa.pub ] && echo True || echo False'
    result = utils.exec_cmd(cmd, ssh_obj)
    result = result.replace(" ", "")
    result = result.replace("\n", "")
    if result == 'False':
        return False
    else:
        return True


def create_id_rsa_pub(ssh_obj):
    """
    Create a new SSH key pair in the /root/.ssh directory if it does not exist.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the key pair is created successfully or already exists, False otherwise.
    """
    cmd = 'ssh-keygen -f /root/.ssh/id_rsa -N ""'
    result = utils.exec_cmd(cmd, ssh_obj)
    if not result:
        return False
    else:
        return True


def revise_sshd_config(ssh_obj):
    """
    Modify the sshd_config file to enable public key authentication.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the sshd_config file is modified successfully, False otherwise.
    """
    cmd = "sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/g' /etc/ssh/sshd_config"
    utils.exec_cmd(cmd, ssh_obj)
    return True


def check_authorized_keys(ssh_obj):
    """
    Check if the authorized_keys file exists in the /root/.ssh directory.

    Args:
        ssh_obj (paramiko.SSHClient): The SSH client object.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    cmd = '[ -f /root/.ssh/authorized_keys ] && echo True || echo False'
    result = utils.exec_cmd(cmd, ssh_obj)
    result = result.replace(" ", "")
    result = result.replace("\n", "")
    if result == 'False':
        return False
    else:
        return True
