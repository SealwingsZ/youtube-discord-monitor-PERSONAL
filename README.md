# YouTube Discord Monitor

ระบบแจ้งเตือนคลิปวิดีโอใหม่และการไลฟ์สดจากช่อง YouTube ไปยัง Discord โดยอัตโนมัติ ผ่าน Discord Webhook และ GitHub Actions

ระบบจะตรวจสอบช่อง YouTube ที่กำหนดไว้ทุก ๆ 5 นาที โดยไม่จำเป็นต้องเปิดคอมพิวเตอร์ทิ้งไว้

## 🌟 ฟีเจอร์หลัก (Key Features)

- ⚡ **Quota Optimized:** ปรับมาใช้ `playlistItems` API (`UU...`) ร่วมกับเทคนิค Batching 50 คลิป/Request ทำให้รองรับ 30+ ช่องโดยใช้โควต้าเพียง ~8,900 / 10,000 Units ต่อวัน
- ⏱️ **Discord Dynamic Timestamps:** แสดงเวลาที่คลิป/ไลฟ์ถูกเผยแพร่จริงบน YouTube แบบเรียลไทม์ ด้วยโครงสร้าง `<t:UNIX:R>` (เช่น *3 minutes ago*)
- 🧹 **Clean Git History:** ระบบจะทำการ `git commit` และ `git push` อัปเดตไฟล์ `state.json` เฉพาะเมื่อพบคลิป/ไลฟ์ใหม่จริงๆ เท่านั้น หมดปัญหาสปัม Commit ทุก 5 นาที
- 📦 **State Auto-Trim:** จำกัดประวัติการบันทึกคลิปย้อนหลังสูงสุด 10 คลิปล่าสุดต่อช่อง เพื่อป้องกันไม่ให้ไฟล์ `state.json` สะสมขนาดใหญ่เกินไป
- ☁️ **Serverless 100%:** ทำงานบน Cloud ของ GitHub Actions และรับสัญญาณ Trigger จาก External Cron (เช่น `cron-job.org`) โดยไม่ต้องเปิดคอมพิวเตอร์ทิ้งไว้

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
├── .github/
│   └── workflows/
│       └── monitor.yml       # ตั้งค่าการรันสคริปต์บน GitHub Actions
├── config.json               # รายชื่อช่อง YouTube และการจัดกลุ่ม Webhook
├── state.json                # บันทึก ID คลิปที่เคยแจ้งเตือนแล้ว (จัดการอัตโนมัติ)
├── monitor.py                # สคริปต์หลักในการดึง API และส่งข้อความเข้า Discord
└── README.md                 # เอกสารอธิบายโปรเจกต์
```

## ⚙️ โครงสร้างไฟล์คีย์หลัก (Configuration)

1. config.json
ใช้กำหนดกลุ่ม Webhook และตั้งค่า channel_id ของ YouTube ที่ต้องการติดตาม:

```json
{
  "groups": {
    "A": {
      "webhook_env": "DISCORD_WEBHOOK_GROUP_A"
    },
    "B": {
      "webhook_env": "DISCORD_WEBHOOK_GROUP_B"
    }
  },
  "channels": [
    {
      "name": "Channel Name A",
      "id": "UCxxxxxxxxxxxxxxxxxxxxxx",
      "group": "A"
    },
    {
      "name": "Channel Name B",
      "id": "UCyyyyyyyyyyyyyyyyyyyyyy",
      "group": "B"
    }
  ]
}
```

2. state.json
ไฟล์บันทึกสถานะเริ่มต้น (สร้างไว้ที่ Root ของโปรเจกต์):

```json
{
  "channels": {}
}
```

## 🚀 ขั้นตอนการตั้งค่าระบบ (Setup Guide)
1. ตั้งค่า GitHub Repository Secrets
ไปที่ Settings > Secrets and variables > Actions บน GitHub แล้วเพิ่ม Secrets ดังนี้ *[1], [2], [3]*:

*[1]* YOUTUBE_API_KEY: API Key จาก Google Cloud Console (เปิดใช้งาน YouTube Data API v3)

```text
ขั้นตอนการเก็บ API Key:
1) เข้าไปที่ Google Cloud Console (https://console.cloud.google.com/)
2) สร้าง Project ใหม่ หรือเลือก Project ที่มีอยู่
3) เปิดใช้งาน **YouTube Data API v3**
4) สร้าง API Key
5) คัดลอก API Key เก็บไว้
```

*[2]* DISCORD_WEBHOOK_GROUP_A: URL ของ Discord Webhook สำหรับกลุ่ม A

*[3]* DISCORD_WEBHOOK_GROUP_B: URL ของ Discord Webhook สำหรับกลุ่ม B (ถ้ามี)

```text
ขั้นตอนการเก็บ URL ของ Discord Webhook:
1) เข้าไปที่ Server ที่ต้องการรับการแจ้งเตือน
2) เลือกห้องข้อความที่ต้องการ
3) เข้าไปที่ Edit Channel
4) เลือก Integrations
5) เลือก Webhooks
6) กด New Webhook
7) คัดลอก Webhook URL เก็บไว้
```

2. ตั้งค่า External Cron Trigger
เนื่องจากระบบเน้นความเสถียรและตรงเวลา จึงใช้บริการ External Cron (เช่น cron-job.org) ยิงมาที่ GitHub Actions ทุกๆ 5 นาที:

```text
1) เข้าไปที่ cron-job (https://console.cron-job.org/)
2) สร้าง cronjob จากนั้นใส่รายละเอียดดังนี้


ส่วน COMMON:

URL: https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches

เปลี่ยน YOUR_USERNAME/YOUR_REPO เป็นของตัวเอง

Execution schedule: ตั้งเวลาการทำงานอัตโนมัติ


ส่วน ADVANCED:

Headers [1], [2], [3]:

[1] Authorization: Bearer (Personal Access Token)

ขั้นตอนการสร้าง Personal Access Token (PAT): 
วิธีที่ 1: Fine-grained Token (แนะนำสำหรับความปลอดภัยสูงสุด)
1) เข้าไปใน Settings ของ GitHub
2) Developer Settings > Personal access tokens > Fine-grained tokens แล้วสร้าง token
Add permissions > Actions > Read and write > Generate token เมื่อสร้างแล้ว ทำการคัดลอกรหัส
(ขึ้นต้นด้วย github_pat_...) แล้วนำไปใส่ใน Header Authorization: Bearer [token]

วิธีที่ 2: Classic Token (ตั้งค่าง่าย ไม่ติดสิทธิ์ย่อย)
1) เข้าไปใน Settings ของ GitHub
2) Developer Settings > Personal access tokens > Tokens(classic) > Generate new token > Generate new token(classic) > ติ๊กถูกช่อง repo > Generate token
เมื่อสร้างแล้ว ทำการคัดลอกรหัส (ขึ้นต้นด้วย ghp_...) นำไปใส่ใน Header Authorization: Bearer [token]

[2] Accept: application/vnd.github.v3+json

[3] User-Agent: cron-job.org (หรือ cron-job-bot)

Request method: POST

Request Body (JSON):

{
  "event_type": "cron_trigger"
}
```

---------------------------
## 🧪 การทดสอบระบบ (Test Run)

หลังจากตั้งค่าใน cron-job.org เสร็จเรียบร้อย ให้กด Save และกด Test run

สามารถตรวจสอบการทำงานได้ที่แท็บ Actions ใน Repository ของคุณบน GitHub จะเห็น Workflow ตื่นขึ้นมารันโดยอัตโนมัติ และจะรันอัตโนมัติทุกๆ 5 นาที

ปล. Project นี้ผู้พัฒนาสร้างขึ้นเพื่อใช้งานสำหรับความสนใจส่วนบุคคล หากคุณต้องการ code template สำหรับนำไปใช้ ผู้พัฒนายินดี แต่ขอแนะนำให้ใช้ code จาก repository 
youtube-discord-notifier (https://github.com/SealwingsZ/youtube-discord-notifier.git) แทน เพราะผู้พัฒนาได้ปรับให้เป็นรูปแบบ default มากกว่า ทำให้สามารถแก้ไขค่าต่างๆได้สะดวกกว่า พร้อมมีวิธีใช้งาน ซึ่งรูปแบบคล้ายๆกันแนบไว้ในไฟล์ README.md

***Thank you.***

---------------------------

### *Q&A (Which I did ask myself)*

> Q1: ทำไมฉันต้องการให้บอทแจ้งเตือนฉันบน Discord ด้วย? ในเมื่อ Youtube เองก็มีระบบแจ้งเตือนเมื่อมีการลงคลิปใหม่ของช่องที่ฉันติดตามอยู่แล้ว

> A1: 1. คุณสามารถได้รับการแจ้งเตือนจากช่องต่างๆ บน Youtube แม้คุณไม่ได้ทำการติดตามไว้ หรือในกรณีที่คุณไม่ได้เข้าสู่ระบบบัญชี Youtube ของคุณบนอุปกรณ์ คุณก็จะสามารถได้รับการแจ้งเตือนโดยตรงผ่าน Discord server ของคุณได้
    2. คุณสามารถแบ่งกลุ่มการแจ้งเตือนได้อย่างอิสระ โดยสามารถเลือกช่องต่างๆ บน Youtube และจัดการแยกให้บอทส่งการแจ้งเตือนไปยังแต่ละแชนแนลที่คุณต้องการบน Discord server ของคุณได้
เช่น ช่อง A,B,C ทำคลิปเกี่ยวกับอาหาร ส่วนช่อง D,E,F ทำคลิปเกี่ยวกับการพัฒนาตนเอง คุณก็สามารถตั้งค่าให้เมื่อช่อง A,B,C ลงคลิปใหม่ บอทจะทำการส่งการแจ้งเตือนทาง Discord ไปยังแชนแนลเกี่ยวกับการทำอาหาร หรืออื่นๆ ตามที่คุณต้องการได้ รวมถึงสามารถใช้เป็นช่องทางการอัพเดตเพื่อพูดคุยเกี่ยวกับคลิปใหม่กับเพื่อนของคุณบน Discord server ได้
    3. แก้ปัญหา Youtube ไม่ส่งการแจ้งเตือนการลงคลิปใหม่ หรือการไลฟ์สดให้ผู้ติดตาม
    4. หากคุณเป็น Youtuber หรือ Content creator ที่มี Discord server สำหรับผู้ติดตามของคุณ คุณสามารถใช้ประโยชน์จากโปรเจกต์นี้สำหรับการส่งการแจ้งเตือนให้อัตโนมัติบน Discord server ของคุณได้ เพื่อให้แฟนคลับของคุณไม่พลาดคลิปใหม่ โดยที่คุณไม่จำเป็นต้องเสียเวลาแจ้งบน Discord ด้วยตนเองทุกครั้ง
    5. โปรเจกต์นี้สามารถนำไปใช้ได้โดยไม่เสียค่าใช้จ่าย

*Next*

> Q2: มันน่าจะมีวิธีที่ดีและประสิทธิภาพสูงกว่านี้รึเปล่า? ทำไมดูใช้อะไรมั่วๆจัง

> A2: มีวิธีที่ดีและประสิทธิภาพสูงกว่าแน่นอน แต่ตัวผู้พัฒนาสร้าง Project นี้ขึ้นมาเพื่อความสนุก, เป็นประสบการณ์ และเพื่อตอบสนองความต้องการส่วนตัวของผู้พัฒนาเท่านั้น และเป้าหมายคือสามารถใช้งานได้ จึงไม่ได้มีการสืบค้นหาวิธีหรือเครื่องมือที่ดีกว่าอย่างจริงจัง

*Next*

> Q3: ทำไ-

>A3: ตามตรงแล้ว ผู้พัฒนาต้องการให้ Project นี้เป็นรูปแบบ Private แต่เนื่องจากการใช้ cron-job.org สำหรับการตรวจสอบอัตโนมัติทุกๆ 5 นาที ทำให้ผู้พัฒนาต้องตั้งค่า Project นี้เป็นรูปแบบ Public

*Next*

> Q4: แล้วทำไมไม่หาวิธีอื่นที่ไม่ต้องตั้ง Project เป็น Public?

> A4: A2

*Next*

> Q5: อธิบายดูดีขนาดนี้ มีข้อจำกัดบ้างไหม?

> A5: มีข้อจำกัด โดยบน Google Cloud Console มีการจำกัด Youtube API ไม่เกิน 10,000 Units ต่อวัน ทำให้มีข้อจำกัดในด้านของจำนวนช่องบน Youtube ที่คุณเลือกให้ตรวจสอบได้ โดยในโปรเจกต์นี้จะจำกัดอยู่ที่ประมาณ 30 ช่อง

---------------------------

### ****Disclaimer: This project was developed with the assistance of AI.****

---------------------------

```
Developer
- SealwingsZ
:33333
```
