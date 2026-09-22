# language: Python 3.10+, file: fix_rsociety.py, target: Windows 10/11
# Deshace todo lo que hizo rsociety_lock.py:
#   - quita persistencia del Run
#   - restaura Task Manager, Regedit, CMD
#   - mata python.exe / pythonw.exe que estén corriendo el locker
#   - relanza explorer.exe si lo mató
#   - borra el .py y .exe del locker (opcional)

import os
import sys
import ctypes
import winreg
import subprocess
import time

LOCKER_NAMES = ["rsociety_lock", "rsociety_lock.py", "rsociety_lock.exe",
                "virusbyR", "virusbyR.py", "virusbyR.exe"]
TASK_NAME = "RsocietyLocker"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate():
    """Relanza el script como admin si no lo está."""
    if not is_admin():
        print("[!] se requiere admin. relanzando con UAC...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            f'"{os.path.abspath(__file__)}"', None, 1)
        sys.exit(0)


def kill_python_processes():
    """Mata python.exe y pythonw.exe excepto este proceso."""
    me = os.getpid()
    for exe in ("python.exe", "pythonw.exe"):
        try:
            out = subprocess.check_output(
                ["wmic", "process", "where", f"name='{exe}'", "get", "ProcessId"],
                text=True, stderr=subprocess.DEVNULL
            )
            for line in out.splitlines():
                line = line.strip()
                if line.isdigit():
                    pid = int(line)
                    if pid == me:
                        continue
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                                   capture_output=True)
                    print(f"[+] matado {exe} pid={pid}")
        except Exception as e:
            print(f"[!] no pude listar {exe}: {e}")


def delete_reg_value(hive, path, name):
    try:
        k = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(k, name)
            print(f"[+] borrado {path}\\{name}")
        except FileNotFoundError:
            print(f"[.] no existía {path}\\{name}")
        winreg.CloseKey(k)
    except FileNotFoundError:
        print(f"[.] no existía la clave {path}")
    except Exception as e:
        print(f"[!] error borrando {path}\\{name}: {e}")


def restore_registry():
    print("\n=== restaurando registro ===")

    # persistencia del Run
    delete_reg_value(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        TASK_NAME,
    )
    delete_reg_value(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        "RsocietyLocker",
    )

    # políticas de bloqueo
    delete_reg_value(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
        "DisableTaskMgr",
    )
    delete_reg_value(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
        "DisableRegistryTools",
    )
    delete_reg_value(
        winreg.HKEY_CURRENT_USER,
        r"Software\Policies\Microsoft\Windows\System",
        "DisableCMD",
    )


def restore_explorer():
    print("\n=== relanzando explorer ===")
    try:
        # si explorer no está, relanzarlo
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq explorer.exe"],
            text=True
        )
        if "explorer.exe" not in out.lower():
            subprocess.Popen(["explorer.exe"])
            print("[+] explorer relanzado")
        else:
            print("[.] explorer ya está corriendo")
    except Exception as e:
        print(f"[!] error: {e}")


def unhook_keyboard():
    """El gancho muere al terminar el proceso, pero por si acaso."""
    print("\n=== liberando gancho de teclado ===")
    try:
        ctypes.windll.user32.UnhookWindowsHookEx(0)
    except Exception:
        pass
    try:
        ctypes.windll.user32.BlockInput(False)
        print("[+] BlockInput desbloqueado")
    except Exception as e:
        print(f"[!] {e}")


def find_and_delete_files():
    """Busca el .py y .exe del locker en el perfil del usuario y los borra."""
    print("\n=== buscando archivos del locker ===")
    home = os.path.expanduser("~")
    hits = []
    for root, dirs, files in os.walk(home):
        # no bajar demasiado profundo ni en AppData/Local/Temp
        if any(skip in root for skip in ("AppData\\Local\\Temp", ".git", "node_modules")):
            continue
        for f in files:
            if f.lower() in [n.lower() for n in LOCKER_NAMES]:
                hits.append(os.path.join(root, f))

    if not hits:
        print("[.] no encontré archivos del locker en", home)
        return

    for path in hits:
        try:
            os.remove(path)
            print(f"[+] borrado {path}")
        except Exception as e:
            print(f"[!] no pude borrar {path}: {e}")


def kill_lock_task():
    """Mata la tarea programada si existe."""
    print("\n=== buscando tarea programada ===")
    try:
        subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                      capture_output=True)
        print(f"[+] tarea {TASK_NAME} eliminada (si existía)")
    except Exception:
        pass


def main():
    elevate()

    print("=" * 60)
    print("RESTAURADOR RSOCIETY LOCK")
    print("=" * 60)

    # 1. matar procesos
    print("\n=== matando python.exe / pythonw.exe ===")
    kill_python_processes()
    time.sleep(1)

    # 2. registro
    restore_registry()

    # 3. explorer
    restore_explorer()

    # 4. gancho
    unhook_keyboard()

    # 5. tarea programada (por si acaso)
    kill_lock_task()

    # 6. archivos
    find_and_delete_files()

    print("\n" + "=" * 60)
    print("LISTO. Reinicia la máquina para asegurar que todo quede limpio.")
    print("=" * 60)


if __name__ == "__main__":
    main()
