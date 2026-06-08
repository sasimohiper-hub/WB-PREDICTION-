// ═══════════════════════════════════════════════
//   WONGBAGUS BOT — Cloudflare Workers
//   Bot: @WongBagusBot
// ═══════════════════════════════════════════════

const BOT_TOKEN = '8993985846:AAGPjybdsW_dsbvz5p_MX7Vz4E2s_VZzk28';
const ADMIN_ID  = 7738360895;
const BOT_API   = `https://api.telegram.org/bot${BOT_TOKEN}`;

// ── KV namespace binding: WBSTORE (daftar member)
// Pastikan KV binding bernama WBSTORE di Cloudflare dashboard

// ────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response('WongBagus Bot aktif ✅', { status: 200 });
    }
    try {
      const update = await request.json();
      await handleUpdate(update, env);
    } catch (e) {
      console.error('Error:', e);
    }
    return new Response('OK', { status: 200 });
  }
};

// ── HANDLE UPDATE ──
async function handleUpdate(update, env) {
  const msg = update.message || update.edited_message;
  if (!msg) return;

  const chatId   = msg.chat.id;
  const userId   = msg.from.id;
  const text     = (msg.text || '').trim();
  const username = msg.from.username ? '@' + msg.from.username : msg.from.first_name;
  const isAdmin  = userId === ADMIN_ID;

  // Simpan member baru otomatis
  await saveMember(env, userId, msg.from.first_name, msg.from.username);

  // ── ROUTING COMMAND ──
  if (text === '/start') {
    await cmdStart(chatId, msg.from.first_name);
  }
  else if (text === '/prediksi') {
    await cmdPrediksi(chatId);
  }
  else if (text === '/member' && isAdmin) {
    await cmdMember(chatId, env);
  }
  else if (text.startsWith('/broadcast ') && isAdmin) {
    const pesan = text.slice('/broadcast '.length);
    await cmdBroadcast(chatId, pesan, env);
  }
  else if (text === '/broadcast' && isAdmin) {
    await sendMsg(chatId, '⚠️ Format: /broadcast [pesan yang mau dikirim]');
  }
  else if (text === '/help') {
    await cmdHelp(chatId, isAdmin);
  }
  else {
    // Pesan bebas — balas dengan menu
    await sendMsg(chatId,
      `Halo ${msg.from.first_name}! 👋\n\nKetik /help untuk melihat menu.`
    );
  }
}

// ── CMD /start ──
async function cmdStart(chatId, firstName) {
  const text =
`⭐ *SELAMAT DATANG DI WONGBAGUS PREDICTION* ⭐

Halo *${firstName}*! 👋

Bot ini menyediakan prediksi togel terpercaya dari rumus formula WongBagus.

📌 *MENU UTAMA:*
/prediksi — Lihat prediksi terbaru
/help — Bantuan & info

🌐 *Website:* https://r-hub.github.io
📢 Prediksi dikirim setiap hari oleh admin.

_Semoga hoki!_ 🍀`;

  await sendMsg(chatId, text, { parse_mode: 'Markdown' });
}

// ── CMD /prediksi ──
async function cmdPrediksi(chatId) {
  const text =
`📊 *PREDIKSI WONGBAGUS HARI INI*

Prediksi terbaru akan dikirim admin setiap hari via broadcast.

Pastikan kamu sudah join bot ini agar tidak ketinggalan! ✅

🌐 Lihat lengkap di: https://r-hub.github.io

_Ketik /help untuk info lebih lanjut._`;

  await sendMsg(chatId, text, { parse_mode: 'Markdown' });
}

// ── CMD /help ──
async function cmdHelp(chatId, isAdmin) {
  let text =
`ℹ️ *BANTUAN WONGBAGUS BOT*

/start — Mulai & info bot
/prediksi — Prediksi terbaru
/help — Menu ini

🌐 Website: https://r-hub.github.io`;

  if (isAdmin) {
    text +=
`\n\n🔑 *MENU ADMIN:*
/member — Lihat jumlah member
/broadcast [pesan] — Kirim pesan ke semua member

📤 *Contoh broadcast:*
\`/broadcast Prediksi HK malam ini: 1234 5678\``;
  }

  await sendMsg(chatId, text, { parse_mode: 'Markdown' });
}

// ── CMD /member (admin only) ──
async function cmdMember(chatId, env) {
  const members = await getAllMembers(env);
  const text =
`👥 *DATA MEMBER*

Total member: *${members.length} orang*

_Member tersimpan otomatis saat pertama kali chat dengan bot._`;
  await sendMsg(chatId, text, { parse_mode: 'Markdown' });
}

// ── CMD /broadcast (admin only) ──
async function cmdBroadcast(chatId, pesan, env) {
  const members = await getAllMembers(env);
  if (members.length === 0) {
    await sendMsg(chatId, '⚠️ Belum ada member terdaftar.');
    return;
  }

  await sendMsg(chatId, `📤 Mengirim ke ${members.length} member...`);

  const broadcastText =
`📢 *BROADCAST WONGBAGUS*\n\n${pesan}\n\n🌐 https://r-hub.github.io`;

  let sukses = 0, gagal = 0;
  for (const member of members) {
    try {
      const res = await sendMsg(member.id, broadcastText, { parse_mode: 'Markdown' });
      if (res.ok) sukses++; else gagal++;
    } catch {
      gagal++;
    }
    // Delay kecil agar tidak kena rate limit Telegram
    await sleep(50);
  }

  await sendMsg(chatId,
    `✅ *Broadcast selesai!*\n\n` +
    `✔️ Berhasil: ${sukses}\n` +
    `❌ Gagal: ${gagal}`,
    { parse_mode: 'Markdown' }
  );
}

// ── MEMBER STORAGE (Cloudflare KV) ──
async function saveMember(env, userId, firstName, username) {
  try {
    const key = `member:${userId}`;
    const existing = await env.WBSTORE.get(key);
    if (!existing) {
      await env.WBSTORE.put(key, JSON.stringify({
        id: userId,
        name: firstName,
        username: username || '',
        joinedAt: new Date().toISOString()
      }));
      // Simpan index list
      const listRaw = await env.WBSTORE.get('member_ids') || '[]';
      const list = JSON.parse(listRaw);
      if (!list.includes(userId)) {
        list.push(userId);
        await env.WBSTORE.put('member_ids', JSON.stringify(list));
      }
    }
  } catch(e) {
    console.error('saveMember error:', e);
  }
}

async function getAllMembers(env) {
  try {
    const listRaw = await env.WBSTORE.get('member_ids');
    if (!listRaw) return [];
    const ids = JSON.parse(listRaw);
    const members = [];
    for (const id of ids) {
      const raw = await env.WBSTORE.get(`member:${id}`);
      if (raw) members.push(JSON.parse(raw));
    }
    return members;
  } catch(e) {
    return [];
  }
}

// ── TELEGRAM API HELPER ──
async function sendMsg(chatId, text, extra = {}) {
  const res = await fetch(`${BOT_API}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, ...extra })
  });
  return res.json();
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}
