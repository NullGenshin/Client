import os
import webview
import configparser
import logging
import datetime
import asyncio
import json
import psutil
from colorlog import ColoredFormatter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import hashlib
import shutil
import subprocess

# Set up logging configuration
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Create formatters
console_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Set up logger
logger = logging.getLogger('GameLauncher')
logger.setLevel(logging.DEBUG)

# Add handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

latest_log = os.path.join(log_directory, 'latest.log')
file_handler = logging.FileHandler(latest_log, mode='w')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Api:
    def __init__(self):
        self._window = None
        self.server_thread = threading.Thread(
            target=lambda: uvicorn.run(app, host="127.0.0.1", port=44332, log_level="error"),
            daemon=True
        )
        self.server_thread.start()
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def set_window(self, window):
        self._window = window
    
    def minimize(self):
        webview.windows[0].minimize()
        logger.debug("Window minimized")
        
    def quit(self):
        if self.is_game_running():
            result = webview.windows[0].evaluate_js('''
                confirm("Warning: The game is currently running. Closing this window will not unpatch the game, which may lead to a ban on official servers. Your internet connection may also be affected. Are you sure you want to proceed? DO NOT continue if you do not know what you are doing. I am not taking responsibility for any bans or problems with your PC.")
            ''')
            if result:
                if self._window:
                    self._window.destroy()
                    logger.debug("Window destroyed")
                else:
                    webview.windows[0].destroy()
                    logger.debug("Window destroyed using webview")
            return
            
        if self._window:
            self._window.destroy()
            logger.debug("Window destroyed")
        else:
            webview.windows[0].destroy()
            logger.debug("Window destroyed using webview")

    def set_setting(self, setting_name, value):
        config = configparser.ConfigParser()
        config.read('settings.ini')
        if 'Game' not in config:
            config.add_section('Game')
        config.set('Game', setting_name, value)
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)
        logger.info(f"Setting saved: {setting_name} = {value}")

    def get_setting(self, setting_name, default=None):
        config = configparser.ConfigParser()
        config.read('settings.ini')
        if 'Game' in config and setting_name in config['Game']:
            value = config['Game'][setting_name]
            logger.debug(f"Setting loaded: {setting_name} = {value}")
            return value
        return default

    def setGamePath(self):
        file_types = ('Genshin Impact Game (*.exe)',)
        default_path = r'C:\Program Files\HoYoPlay\games\Genshin Impact game'
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types,
            directory=default_path
        )
        if result and len(result) > 0:
            self.set_setting('gamePath', os.path.dirname(result[0]))
            self.set_setting('gameExecutable', os.path.basename(result[0]))
        logger.debug(f"File dialog result: {result}")

    def is_game_running(self):
        game_executable = self.get_setting('gameExecutable')
        if not game_executable:
            return False
            
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == game_executable.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
        return False    
    def get_patch_dll(self):
        patch_dir = './patch'
        if os.path.exists(patch_dir):
            for file in os.listdir(patch_dir):
                if file.endswith('.dll'):
                    return file
        return ""

    def get_patch_hash(self):
        patch_dir = './patch'
        if os.path.exists(patch_dir):
            for file in os.listdir(patch_dir):
                if file.endswith('.dll'):
                    with open(os.path.join(patch_dir, file), 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    return file_hash[:6]
        return ""
    
    def get_game_patch_hash(self):
        game_dir = self.get_setting('gamePath')
        if not game_dir or not os.path.exists(game_dir):
            return ""
            
        plugin_dir = os.path.join(game_dir, "GenshinImpact_Data", "Plugins")
        astrolabe_path = os.path.join(plugin_dir, "Astrolabe.dll")
        
        if os.path.exists(astrolabe_path):
            with open(astrolabe_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash[:6]
        return ""
    
    def patch_game(self):
        dll_file = self.get_patch_dll()
        dll_hash = self.get_patch_hash()
        game_dir = self.get_setting('gamePath')
        
        if not game_dir or not os.path.exists(game_dir):
            logger.error("Game directory not found")
            return
            
        plugin_dir = os.path.join(game_dir, "GenshinImpact_Data", "Plugins")
        astrolabe_path = os.path.join(plugin_dir, "Astrolabe.dll")
        
        if os.path.exists(astrolabe_path):
            with open(astrolabe_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()[:6]
            
            if current_hash != dll_hash:
                os.makedirs('./patch', exist_ok=True)
                backup_path = os.path.join('./patch', 'Astrolabe.dll.original')
                shutil.copy2(astrolabe_path, backup_path)
                shutil.copy2(os.path.join('./patch', dll_file), astrolabe_path)

    def unpatch_game(self):
        dll_hash = self.get_patch_hash()
        game_dir = self.get_setting('gamePath')
        
        if not game_dir or not os.path.exists(game_dir):
            logger.error("Game directory not found")
            return
            
        plugin_dir = os.path.join(game_dir, "GenshinImpact_Data", "Plugins")
        astrolabe_path = os.path.join(plugin_dir, "Astrolabe.dll")
        backup_path = os.path.join('./patch', 'Astrolabe.dll.original')
        
        if os.path.exists(backup_path):
            with open(backup_path, 'rb') as f:
                original_hash = hashlib.sha256(f.read()).hexdigest()[:6]
            
            if original_hash != dll_hash:
                shutil.copy2(backup_path, astrolabe_path)
                os.remove(backup_path)
            else:
                logger.error("Failed to unpatch - backup file appears to be patched version")
                return
            
    def launch_game(self):
        self.minimize()
        gameDir = self.get_setting('gamePath')
        gameExecutable = self.get_setting('gameExecutable')
        
        if gameDir and gameExecutable:
            game_path = os.path.join(gameDir, gameExecutable)
            self.patch_game()
            
            # Kill any existing mitmdump processes
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'mitmdump.exe':
                    proc.kill()
            
            # Configure Windows proxy settings
            subprocess.run(['reg', 'add', 'HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings', '/v', 'ProxyEnable', '/t', 'REG_DWORD', '/d', '1', '/f'])
            subprocess.run(['reg', 'add', 'HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings', '/v', 'ProxyServer', '/t', 'REG_SZ', '/d', '127.0.0.1:8080', '/f'])
            
            # Install root certificate
            result = subprocess.run(['certutil', '-addstore', 'root', './proxy/root-ca.crt'], shell=True, capture_output=True)
            print(result.stdout.decode('cp866'))
            
            # Start mitmdump with certificate and key
            mitmdump_path = os.path.abspath('./proxy/mitmdump.exe')
            proxy_script = os.path.abspath(os.path.join('proxy', 'proxy.py'))
            proxy_process = subprocess.Popen([
                mitmdump_path,
                '-s', proxy_script,
                '-k',
                '--certs', os.path.abspath('./proxy/leaf-combined.pem'),
                '--allow-hosts', '.*\.yuanshen\.com|.*\.mihoyo\.com|.*\.hoyoverse\.com',
                '--ssl-insecure',
                '--set', 'ip=127.0.0.1',
                '--set', 'port=8088',
                '--set', 'use_https=false'
            ])
            
            game_process = subprocess.Popen([game_path])
            logger.info("Game Launched!")
            
            # Wait for game process to exit
            game_process.wait()
            
            # After game exits, unpatch
            self.unpatch_game()
            
            # Disable Windows proxy settings
            subprocess.run(['reg', 'add', 'HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings', '/v', 'ProxyEnable', '/t', 'REG_DWORD', '/d', '0', '/f'])
            
            # Terminate proxy process
            proxy_process.terminate()

    def kill_game(self):
        gameExecutable = self.get_setting('gameExecutable')
        if gameExecutable:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == gameExecutable:
                    proc.kill()

    def openUrl(self, url):
        webview.windows[0].evaluate_js(f'window.open("{url}", "_blank")')
        logger.info(f"Opening download URL: {url}")

api = Api()
window = webview.create_window(
    'NullGenshin Launcher',
    url='web/index.html',
    width=1280,
    height=720,
    resizable=False,
    frameless=True,
    js_api=api
)
api.set_window(window)
logger.info("Window created successfully")
logger.debug("API exposed")
logger.info("Starting webview")
webview.start(debug=False)