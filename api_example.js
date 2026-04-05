
const API_BASE_URL = 'tribexapi-jwnyk62fq-blazetgt-1180s-projects.vercel.app'; // Replace with your actual URL


 * @param { string } uid - The player's UID.
    * @param { string } region - The player's region (e.g., 'IND', 'BR', 'US').
        * @returns { Promise < Object >} The account information.
 */
async function getAccountInfo(uid, region) {
    const url = `${API_BASE_URL}/info?uid=${uid}&region=${region}`;

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching account info:', error.message);
        throw error;
    }
}

// --- Usage Example ---

const playerUid = '3692279677';
const playerRegion = 'IND';

// Calling the function
getAccountInfo(playerUid, playerRegion)
    .then(data => {
        console.log('Account Data:', data);

        // Example: Accessing specific fields
        if (data.basic_info) {
            console.log('Player Name:', data.basic_info.nickname);
            console.log('Level:', data.basic_info.level);
        }

        if (data.clan_info) {
            console.log('Clan Name:', data.clan_info.clanName);
        }
    })
    .catch(err => {
        console.log('Failed to load player data.');
    });

/**
 * Bonus: Refresh Tokens
 * You can call this periodically or manually if tokens expire.
 */
async function refreshTokens() {
    try {
        const response = await fetch(`${API_BASE_URL}/refresh`);
        const result = await response.json();
        console.log('Refresh result:', result.message);
    } catch (error) {
        console.error('Refresh failed:', error);
    }
}
