# Discord bot for STON.fi
This bot is designed for STON.fi (DEX on TON blockchain) <a href="https://discord.gg/stonfi">Discord server</a>. It has the following features implemented:
- Connecting Tonkeeper to a Discord account.
- Tracking the volume of swaps on DEX, made from the connected wallet.
- Verification that the user owns various NFTs.
- Automatic role assignment on the server if the user meets the conditions for swap volume/NFT hold.
- The ability to automatically remove roles from all users who no longer meet the conditions.

The code is written in python using the following libraries:
- <a href="https://github.com/ClickoTON-Foundation/tonconnect">tonconnect</a> 
- <a href="https://github.com/Rapptz/discord.py">discord.py</a>
- <a href="https://github.com/lincolnloop/python-qrcode">qrcode</a>
- requests
- multiprocessing
- os
- time
