window.addEventListener('pywebviewready', function() {
    window.toggleSettings = function() {
        const settingsMenu = document.getElementById('settingsMenu');
        const settingsBtn = document.querySelector('.settings-btn');
        
        if (settingsMenu.style.display === 'none' || !settingsMenu.style.display) {
            settingsMenu.style.display = 'block';
            settingsBtn.classList.add('active');
        } else {
            settingsMenu.style.display = 'none';
            settingsBtn.classList.remove('active');
        }
    }

    async function updateGameStatus() {
        const isRunning = await window.pywebview.api.is_game_running();
        document.getElementById('gameStatus').textContent = 'Status: ' + (isRunning ? 'Running' : 'Not Running');
        const killButton = document.querySelector('.kill-btn');
        killButton.style.display = isRunning ? 'inline-block' : 'none';
    }

    async function updatePatchName() {
        const patchName = await window.pywebview.api.get_patch_dll()
        document.getElementById('patchName').textContent = 'Patch: ' + patchName;
    }

    async function updatePatchHash() {
        const patchHash = await window.pywebview.api.get_patch_hash()
        document.getElementById('patchHash').textContent = 'Patch: ' + patchHash;
    }

    async function updateGamePatchHash() {
        const gamePatchHash = await window.pywebview.api.get_game_patch_hash()
        document.getElementById('gamePatchHash').textContent = 'Game hash: ' + gamePatchHash;
    }

    async function updatePatchHash() {
        const patchHash = await window.pywebview.api.get_patch_hash()
        document.getElementById('patchHash').textContent = 'Patch hash: ' + patchHash;
    }

    // Update game status every second
    setInterval(updateGameStatus, 1000);
    setInterval(updatePatchName, 1000);
    setInterval(updateGamePatchHash, 1000);
    setInterval(updatePatchHash, 1000);
});