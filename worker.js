// ═══════════════════════════════════════════════
//   WONGBAGUS BOT — Cloudflare Workers
//   Bot: @WongBagusBot
//   UPDATE: Support Bank Rumus JSON
// ═══════════════════════════════════════════════

const BOT_TOKEN = '8993985846:AAGPjybdsW_dsbvz5p_MX7Vz4E2s_VZzk28';
const ADMIN_ID  = 7738360895;
const BOT_API   = `https://api.telegram.org/bot${BOT_TOKEN}`;
const WEB_URL   = 'https://sasimohiper-hub.github.io/WB-PREDICTION-/';

// ── KV namespace binding: WBSTORE
// Pastikan KV binding bernama WBSTORE di Cloudflare dashboard

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

  // ── ADMIN: Terima file JSON bank rumus ──
  if (isAdmin && msg.document) {
    const doc = msg.document;
    if (doc.file_name && doc.file_name.endsWith('.json')) {
      await handleBankRumusUpload(chatId, doc, env);
      return;
    }
  }

  // ── ROUTING COMMAND ──
  if (text === '/start') {
    await cmdStart(chatId, msg.from.first_name);
  }
  else if (text === '/prediksi') {
    await cmdPrediksi(chatId, env);
  }
  else if (text === '/member' && isAdmin) {
    await cmdMember(chatId, env);
  }
  else if (text.startsWith('/broadcast ') && isAdmin) {
    const pesan = text.slice('/broadcast '.length);
    await cmdBroadcast(chatId, pesan, env);
  }
  else if (text === '/broadcastrumus' && isAdmin) {
    await cmdBroadcastRumus(chatId, env);
  }
  else if (text === '/broadcast' && isAdmin) {
    await sendMsg(chatId, '⚠️ Format: /broadcast [pesan yang mau dikirim]');
  }
  else if (text === '/help') {
    await cmdHelp(chatId, isAdmin);
  }
  else {
    await sendMsg(chatId,
      `Halo ${msg.from.first_name}! 👋\n\nKetik /help untuk melihat menu.`
    );
  }
}

// ── HANDLE UPLOAD FILE JSON BANK RUMUS (ADMIN) ──
async function handleBankRumusUpload(chatId, doc, env) {
  try {
    await sendMsg(chatId, '⏳ Memproses file bank rumus...');

    // Download file dari Telegram
    const fileInfoRes = await fetch(`${BOT_API}/getFile?file_id=${doc.file_id}`);
    const fileInfo = await fileInfoRes.json();
    if (!fileInfo.ok) {
      await sendMsg(chatId, '❌ Gagal ambil file dari Telegram.');
      return;
    }

    const fileUrl = `https://api.telegram.org/file/bot${BOT_TOKEN}/${fileInfo.result.file_path}`;
    const fileRes = await fetch(fileUrl);
    const rawText = await fileRes.text();
    const bankData = JSON.parse(rawText);

    if (!bankData.data || !Array.isArray(bankData.data)) {
      await sendMsg(chatId, '❌ Format JSON tidak valid. Pastikan ada field "data" berisi array rumus.');
      return;
    }

    // Simpan ke KV
    await env.WBSTORE.put('bank_rumus', JSON.stringify(bankData));

    const count = bankData.data.length;
    await sendMsg(chatId,
      `✅ *Bank Rumus berhasil disimpan!*\n\n` +
      `📦 Total rumus: *${count}*\n` +
      `🕐 Disimpan: ${new Date().toLocaleString('id-ID')}\n\n` +
      `Ketik /prediksi untuk preview, atau /broadcastrumus untuk kirim ke semua member.`,
      { parse_mode: 'Markdown' }
    );

  } catch (e) {
    console.error('handleBankRumusUpload error:', e);
    await sendMsg(chatId, '❌ Gagal proses file: ' + e.message);
  }
}

// ── LABEL JENIS RUMUS ──
function getJenisLabel(jenis) {
  const map = {
    ai_ke: 'AI KE', ai_ac: 'AI AC', ai_ck: 'AI CK',
    bbfs_ke: 'BBFS KE', bbfs_ac: 'BBFS AC', bbfs_ck: 'BBFS CK',
    bbfs_4d: 'BBFS 432D',
    pos_e: 'Posisi Ek', pos_k: 'Posisi Kp',
    pos_a: 'Posisi As', pos_c: 'Posisi Cp'
  };
  return map[jenis] || (jenis||'AI').toUpperCase();
}

// ── LABEL PENDEK (untuk kolom di baris trek) ──
function getRowLabel(jenis) {
  const map = {
    ai_ke: 'ai', ai_ac: 'ai', ai_ck: 'ai',
    bbfs_ke: 'bbfs', bbfs_ac: 'bbfs', bbfs_ck: 'bbfs',
    bbfs_4d: '432d',
    pos_e: 'e', pos_k: 'k', pos_a: 'a', pos_c: 'c'
  };
  return map[jenis] || 'ai';
}

// ── FORMAT SATU RUMUS JADI TEKS ──
// Format persis seperti tampilan trek modal di screenshot
function formatRumus(item) {
  const wbLabel  = getWbLabel(item.wbId);
  const jenisLabel = getJenisLabel(item.jenis);
  const rowLabel   = getRowLabel(item.jenis);
  const hitCount   = item.acc || 0;
  const patahCount = item.maxPatah || 0;
  const limit      = item.limit || 12;

  // Header
  let text = `${wbLabel}\n\n`;
  text += `Code : ${item.formula}\n`;
  text += `Rumus : ${jenisLabel}\n`;
  text += `HIT: ${hitCount}   PATAH: ${patahCount}x\n\n`;

  // Baris history trek (jika ada field trek di item)
  if (item.trek && Array.isArray(item.trek) && item.trek.length > 0) {
    for (const row of item.trek) {
      const period = String(row.period||'').padStart(4,'0');
      const pred   = row.pred || '--';
      if (row.isNext) {
        text += `${period}  :  ${pred}   ?   ??\n`;
      } else {
        const status = row.hit ? '✅' : '❌';
        text += `${period}  :  ${pred}   ${rowLabel}   ${status}\n`;
      }
    }
    text += '\n';
  }

  // Footer prediksi
  text += `${jenisLabel} : ${item.predNow}\n`;
  text += `===============\n`;
  text += `${limit} putaran | patah ${patahCount}x`;

  return text;
}

// ── LABEL PASARAN ──
function getWbLabel(wbId) {
  const map = {
    hk: '🇭🇰 Hongkong (HK)',
    sgp: '🇸🇬 Singapore (SGP)',
    sdy: '🇦🇺 Sydney (SDY)',
    macau: '🎰 Macau',
    taiwan: '🇹🇼 Taiwan',
  };
  return map[wbId] || `🌐 ${wbId.toUpperCase()}`;
}

// ── CMD /prediksi — tampilkan dari bank rumus ──
async function cmdPrediksi(chatId, env) {
  try {
    const raw = await env.WBSTORE.get('bank_rumus');
    if (!raw) {
      await sendMsg(chatId,
        `📊 *PREDIKSI WONGBAGUS*\n\nPrediksi belum tersedia.\nAdmin akan segera mengupdate.\n\n🌐 ${WEB_URL}`,
        { parse_mode: 'Markdown' }
      );
      return;
    }

    const bankData = JSON.parse(raw);
    const items = bankData.data;

    // Kirim tiap rumus satu per satu (format trek modal)
    for (const item of items) {
      const text = formatRumus(item);
      await sendMsg(chatId, text);
      await sleep(300);
    }

    await sendMsg(chatId,
      `🌐 Lihat lengkap: ${WEB_URL}`,
      {
        reply_markup: {
          inline_keyboard: [[
            { text: '🌐 Buka WongBagus Prediction', url: WEB_URL }
          ]]
        }
      }
    );

  } catch (e) {
    console.error('cmdPrediksi error:', e);
    await sendMsg(chatId, '❌ Gagal load prediksi: ' + e.message);
  }
}

// ── CMD /broadcastrumus — kirim prediksi ke semua member ──
async function cmdBroadcastRumus(chatId, env) {
  try {
    const raw = await env.WBSTORE.get('bank_rumus');
    if (!raw) {
      await sendMsg(chatId, '⚠️ Bank rumus kosong. Upload dulu file JSON bank rumus.');
      return;
    }

    const bankData = JSON.parse(raw);
    const items = bankData.data;
    const members = await getAllMembers(env);

    if (members.length === 0) {
      await sendMsg(chatId, '⚠️ Belum ada member terdaftar.');
      return;
    }

    await sendMsg(chatId, `📤 Mulai broadcast ke ${members.length} member...`);

    let sukses = 0, gagal = 0;

    for (const member of members) {
      try {
        // Header broadcast
        await sendMsg(member.id,
          `📢 PREDIKSI WONGBAGUS\n🗓 ${new Date().toLocaleDateString('id-ID', { weekday:'long', year:'numeric', month:'long', day:'numeric' })}`
        );
        await sleep(100);

        // Kirim tiap rumus satu per satu, format trek modal
        for (const item of items) {
          const text = formatRumus(item);
          await sendMsg(member.id, text);
          await sleep(150);
        }

        // Footer
        await sendMsg(member.id, `🌐 ${WEB_URL}`, {
          reply_markup: {
            inline_keyboard: [[
              { text: '🌐 Buka WongBagus Prediction', url: WEB_URL }
            ]]
          }
        });

        sukses++;
      } catch {
        gagal++;
      }
      await sleep(200);
    }

    await sendMsg(chatId,
      `✅ *Broadcast selesai!*\n\n✔️ Berhasil: ${sukses}\n❌ Gagal: ${gagal}`,
      { parse_mode: 'Markdown' }
    );

  } catch (e) {
    console.error('cmdBroadcastRumus error:', e);
    await sendMsg(chatId, '❌ Error broadcast: ' + e.message);
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

🌐 *Website:* ${WEB_URL}
📢 Prediksi dikirim setiap hari oleh admin.

_Semoga hoki!_ 🍀`;

  await sendMsg(chatId, text, {
    parse_mode: 'Markdown',
    reply_markup: {
      inline_keyboard: [[
        { text: '🌐 Buka WongBagus Prediction', url: WEB_URL }
      ]]
    }
  });
}

// ── CMD /help ──
async function cmdHelp(chatId, isAdmin) {
  let text =
`ℹ️ *BANTUAN WONGBAGUS BOT*

/start — Mulai & info bot
/prediksi — Prediksi terbaru
/help — Menu ini

🌐 Website: ${WEB_URL}`;

  if (isAdmin) {
    text +=
`\n\n🔑 *MENU ADMIN:*
/member — Lihat jumlah member
/broadcast [pesan] — Kirim pesan bebas ke semua member
/broadcastrumus — Kirim prediksi dari bank rumus ke semua member

📤 *Cara update prediksi:*
1. Kirim file JSON bank rumus ke bot ini
2. Bot otomatis simpan
3. Ketik /broadcastrumus untuk kirim ke semua member`;
  }

  await sendMsg(chatId, text, {
    parse_mode: 'Markdown',
    reply_markup: {
      inline_keyboard: [[
        { text: '🌐 Buka WongBagus Prediction', url: WEB_URL }
      ]]
    }
  });
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

// ── CMD /broadcast teks bebas (admin only) ──
async function cmdBroadcast(chatId, pesan, env) {
  const members = await getAllMembers(env);
  if (members.length === 0) {
    await sendMsg(chatId, '⚠️ Belum ada member terdaftar.');
    return;
  }

  await sendMsg(chatId, `📤 Mengirim ke ${members.length} member...`);

  const broadcastText =
`📢 *BROADCAST WONGBAGUS*\n\n${pesan}\n\n🌐 ${WEB_URL}`;

  let sukses = 0, gagal = 0;
  for (const member of members) {
    try {
      const res = await sendMsg(member.id, broadcastText, { parse_mode: 'Markdown' });
      if (res.ok) sukses++; else gagal++;
    } catch {
      gagal++;
    }
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
