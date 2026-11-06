# YouTube Discord Monitor [Sealwings's PERSONAL Project]

ระบบแจ้งเตือนคลิปวิดีโอใหม่และการไลฟ์สดจากช่อง YouTube ไปยัง Discord โดยอัตโนมัติ ผ่าน Discord Webhook และ GitHub Actions

ระบบจะทำการตรวจสอบช่อง YouTube ที่กำหนดไว้ทุก ๆ 5 นาที โดยไม่จำเป็นต้องเปิดคอมพิวเตอร์ทิ้งไว้

> Project นี้พัฒนาขึ้นเพื่อการใช้งานส่วนตัวเป็นหลัก หากต้องการ code template สำหรับนำไปปรับใช้หรือศึกษาต่อ ผู้พัฒนายินดีและสามารถทำได้ตามสะดวก แต่ขอแนะนำให้ใช้ code จาก Repository /youtube-discord-notifier (https://github.com/SealwingsZ/youtube-discord-notifier.git) แทน เพราะผู้พัฒนาได้ปรับ code ให้เป็นรูปแบบ default ซึ่งทำให้สะดวกต่อการแก้ไขค่าต่างๆมากกว่า พร้อมมีวิธีการใช้งาน ซึ่งเป็นรูปเดียวกันซึ่งได้แนบไว้ในไฟล์ README.md ของ Repository นั้นแล้ว

---------------------------

### *Q&A (Which I did ask myself)*
This section was made 100% by humans.

> Q1: ทำไมฉันต้องการให้บอทแจ้งเตือนฉันบน Discord ด้วย? ในเมื่อ Youtube เองก็มีระบบแจ้งเตือนเมื่อมีการลงคลิปใหม่ของช่องที่ฉันติดตามอยู่แล้ว

> A1:
> 1. คุณสามารถได้รับการแจ้งเตือนจากช่องต่างๆ บน Youtube แม้คุณไม่ได้ทำการติดตามไว้ หรือในกรณีที่คุณไม่ได้เข้าสู่ระบบบัญชี Youtube ของคุณบนอุปกรณ์ คุณก็จะสามารถได้รับการแจ้งเตือนโดยตรงผ่าน Discord server ของคุณได้
> 2. คุณสามารถแบ่งกลุ่มการแจ้งเตือนได้อย่างอิสระ โดยสามารถเลือกช่องต่างๆ บน Youtube และจัดการแยกให้บอทส่งการแจ้งเตือนไปยังแต่ละแชนแนลที่คุณต้องการบน Discord server ของคุณได้
>    * **ตัวอย่าง:** ช่อง A,B,C ทำคลิปเกี่ยวกับอาหาร ส่วนช่อง D,E,F ทำคลิปเกี่ยวกับการพัฒนาตนเอง คุณก็สามารถตั้งค่าให้เมื่อช่อง A,B,C ลงคลิปใหม่ บอทจะทำการส่งการแจ้งเตือนทาง Discord ไปยังแชนแนลเกี่ยวกับการทำอาหาร หรืออื่นๆ ตามที่คุณต้องการได้ รวมถึงสามารถใช้เป็นช่องทางการอัพเดตเพื่อพูดคุยเกี่ยวกับคลิปใหม่กับเพื่อนของคุณบน Discord server ได้
> 3. แก้ปัญหา Youtube ไม่ส่งการแจ้งเตือนการลงคลิปใหม่ หรือการไลฟ์สดให้ผู้ติดตาม
> 4. หากคุณเป็น Youtuber หรือ Content creator ที่มี Discord server สำหรับผู้ติดตามของคุณ คุณสามารถใช้ประโยชน์จาก Project นี้สำหรับการส่งการแจ้งเตือนให้อัตโนมัติบน Discord server ของคุณได้ เพื่อให้แฟนคลับของคุณไม่พลาดคลิปใหม่ โดยที่คุณไม่จำเป็นต้องเสียเวลาแจ้งบน Discord ด้วยตนเองทุกครั้ง
> 5. Project นี้สามารถนำไปใช้ได้โดยไม่เสียค่าใช้จ่าย

*Next*

> Q2: มันน่าจะมีวิธีที่ดีและประสิทธิภาพสูงกว่านี้รึเปล่า? ทำไมดูใช้อะไรมั่วๆจัง

> A2: มีวิธีที่ดีและประสิทธิภาพสูงกว่าแน่นอน แต่ตัวผู้พัฒนาสร้าง Project นี้ขึ้นมาเพื่อความสนุก, เป็นประสบการณ์ และเพื่อตอบสนองความต้องการส่วนตัวของผู้พัฒนาเท่านั้น และเป้าหมายคือสามารถใช้งานได้ จึงไม่ได้มีการสืบค้นหาวิธีหรือเครื่องมือที่ดีกว่าอย่างจริงจัง

*Next*

> Q3: ทำไ-

>A3: ตามตรงแล้ว ผู้พัฒนาต้องการให้ Project นี้เป็นรูปแบบ Private แต่เนื่องจากโควต้าของ Github Actions ที่จำกัดอยู่ที่ 2000 นาที/เดือน สำหรับ Private Repository และจากที่ผู้พัฒนาต้องการให้มีการตรวจสอบทุกๆ 5 นาที ทำให้ผู้พัฒนาจำเป็นต้องตั้งค่า Project นี้เป็นรูปแบบ Public เพื่อให้สามารถรันบน GitHub Actions ได้ฟรีแบบไม่จำกัดเวลา

*Next*

> Q4: แล้วทำไมไม่หาวิธีอื่นที่ไม่ต้องตั้ง Project เป็น Public?

> A4: A2

*Next*

> Q5: อธิบายดูดีขนาดนี้ มีข้อจำกัดบ้างไหม?

> A5: มีข้อจำกัด โดย Youtube Data API v3 มีกำหนดโควต้าฟรีไว้ที่ 10,000 Units ต่อวัน ทำให้มีข้อจำกัดในด้านของจำนวนช่องบน Youtube ที่คุณสามารถเลือกตรวจสอบ โดยใน Project นี้จะจำกัดอยู่ที่ประมาณ 30 ช่อง *(หมายเหตุ: คุณสามารถเพิ่มช่อง Youtube มากกว่า 30 ช่องได้ แต่อาจทำให้โควต้าหมดเร็ว ส่งผลให้ workflow หยุดการทำงานระหว่างวันได้)

*Next*

> Q6: ทำไมฉันต้องเลือกใช้โปรเจคนี้แทนบอทสำเร็จที่มีอยู่แล้วและตั้งค่าง่ายกว่า เช่น Pingcord bot หรืออื่นๆ

> A6: Project นี้เน้นความยืดหยุุ่น เพราะสามารถ customize ได้เองเกือบทุกอย่าง และสำหรับตัวผู้พัฒนาเองที่ชื่นชอบความอิสระ บอทที่สามารถเลือกปรับแต่ง pattern การแจ้งเตือนหรืออื่นๅ ได้แทบทั้งหมดจึงตอบโจทย์ผู้พัฒนาอย่างมาก และผู้พัฒนาเชื่อว่ามีผู้ใช้อีกหลายท่านที่ต้องการความเป็นอิสระสูงในการใช้งานเช่นเดียวกัน

---------------------------

## 🌟 ฟีเจอร์หลัก (Key Features)

⚡ Performance & Quota Efficiency
- **Quota Optimized:** ใช้ playlistItems API (UU...) ร่วมกับเทคนิค Batching ดึงข้อมูลสูงสุด 50 คลิป/Request ช่วยลดการใช้ API Quota ให้ครอบคลุม 30+ ช่องโดยใช้โควต้าเพียง ~8,900 / 10,000 Units ต่อวัน
- **State Auto-Trim:** บันทึกประวัติคลิปล่าสุดย้อนหลังสูงสุด 10 คลิปต่อช่อง ป้องกันไฟล์ state.json สะสมขนาดใหญ่เกินไป
- **100% Serverless:** ทำงานบน Cloud ของ GitHub Actions รับสัญญาณ Trigger จาก External Cron โดยไม่ต้องเปิดคอมพิวเตอร์ทิ้งไว้

🎨 Discord Aesthetics & Smart Routing
- **Discord Dynamic Timestamps:** แสดงเวลาเผยแพร่จริงของคลิป/ไลฟ์บน YouTube แบบเรียลไทม์
- **Multi-Group Webhook Routing:** แยกแชนเนลแจ้งเตือนตามกลุ่มของช่อง (เช่น Group A, Group B) พร้อมปรับแต่งคำเกริ่นนำ (Header) แยกตามกลุ่มได้อย่างอิสระ
- **Live Status Dashboard:** ตารางสรุปสถานะการติดตามช่อง และการตรวจสอบ Webhook Environment Variables ลงทั้ง Console Log และ GitHub Job Summary

🚨 Error Handling & System Resilience
- **Dedicated Error Alerting:** รองรับการแยกส่งแจ้งเตือนระบบขัดข้อง รวมถึงการแจ้งเตือนเมื่อระบบล่มชั่วคราว
- **6-Hour Anti-Spam Cooldown:** บันทึกสถานะ Error ล่าสุดลง state.json เพื่อป้องกันการยิงข้อความแจ้งเตือน Error ซ้ำรบกวนใน Discord ทุกๆ 5 นาทีเมื่อ Cronjob รันล้มเหลวต่อเนื่อง
- **Auto-Recovery Notification:** ส่งแจ้งเตือน System Recovery เข้า Discord อัตโนมัติทันทีที่ระบบแก้ไขปัญหาสำเร็จ และกลับมารันได้ตามปกติ

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
ไฟล์บันทึกสถานะเริ่มต้น (สร้างไว้ที่ Root ของ Project):

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

*[Optional]* DISCORD_WEBHOOK_GROUP_B: URL ของ Discord Webhook สำหรับกลุ่ม B

*[Optional]* DISCORD_WEBHOOK_ERROR: URL ของ Discord Webhook สำหรับรับแจ้งเตือนข้อผิดพลาดระบบ (หากไม่ได้กำหนดไว้ การแจ้งเตือนจะถูกส่งไปยัง Group A โดยอัตโนมัติ)

```text
ขั้นตอนการเก็บ URL ของ Discord Webhook:
1) เข้าไปที่ Server ที่ต้องการรับการแจ้งเตือน
2) เลือกห้องข้อความที่ต้องการ
3) เข้าไปที่ Edit Channel
4) เลือก Integrations
5) เลือก Webhooks
6) สร้าง New Webhook
7) คัดลอก Webhook URL เก็บไว้
```

2. ตั้งค่า External Cron Trigger
เนื่องจากระบบเน้นความเสถียรและตรงเวลา จึงใช้บริการ External Cron (เช่น cron-job.org) ยิงมาที่ GitHub Actions ทุกๆ 5 นาที:

...
1) เข้าไปที่ cron-job (https://console.cron-job.org/)
2) สร้าง cronjob จากนั้นใส่รายละเอียดดังนี้

```text
ส่วน COMMON:

URL: https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches

เปลี่ยน YOUR_USERNAME/YOUR_REPO เป็นของตัวเอง

Execution schedule: ตั้งเวลาการทำงานอัตโนมัติ
```

```text
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
> ⚠️ **หมายเหตุ (Repository Visibility & Permissions):**
> หากต้องการให้ Repository เป็น **Private** ไม่ว่าจะเป็นเรื่องข้อจำกัดเวลาของ GitHub Actions หรือไม่ก็ตาม ต้องแน่ใจว่าได้ตั้งค่าสิทธิ์ Personal Access Token (PAT) ให้มีสิทธิ์ `contents: write` และ `actions: write` อย่างถูกต้อง (อย่างไรก็ตาม แนะนำให้ตั้งค่า Repository เป็น **Public** เพื่อการใช้งาน GitHub Actions รันฟรีได้ไม่จำกัดเวลา)
---------------------------
## 🧪 การทดสอบระบบ (Test Run)

หลังจากตั้งค่าใน cron-job.org เสร็จเรียบร้อย ให้กด Save และกด Test run

สามารถตรวจสอบการทำงานได้ที่แท็บ Actions ใน Repository ของคุณบน GitHub จะเห็น Workflow ตื่นขึ้นมารันโดยอัตโนมัติ และจะรันอัตโนมัติทุกๆ 5 นาที

***Thank you.***

---------------------------

### ****Disclaimer: This Project was developed with the assistance of AI.****

---------------------------

```
Developer
- SealwingsZ /•᷅‎‎•᷄\੭
:33333
```
---------------------------

### *⋆ Project Timeline & History⋆*
- Project Created: `03/11/2026`
- Main Code Complete: `04/11/2026`
- 1st Refactor (Add Error Handling): `05/11/2026`

---------------------------

### ❓ปัญหาที่พบบ่อย (Troubleshooting & Common Issues)

หากตั้งค่าตามคู่มือแล้วเกิด Error หรือระบบไม่ส่งแจ้งเตือน ตรวจสอบจุดที่มักจะมองข้ามเหล่านี้:

1. **GitHub Actions / Cron Trigger ขึ้น Error (401 / 404 / Unauthorized)**
   - ตรวจสอบสิทธิ์ Personal Access Token (PAT) ว่าเปิดสิทธิ์ `contents: write` และ `actions: write` แล้วหรือยัง
   - ตรวจสอบ URL ของ Repository ใน `cron-job.org` ว่าพิมพ์ถูกต้องตามรูปแบบ (`https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches`)

2. **บอทหยุดทำงานหลังจากผ่านไปประมาณ 7 วัน (กรณี Private Repository)**
   - Repository แบบ Private จะมีโควต้ารัน GitHub Actions ฟรีเพียง 2,000 นาที/เดือน การสั่งรันทุก 5 นาทีจะทำให้โควต้าหมดอย่างรวดเร็ว แนะนำให้เปลี่ยน Repository Visibility เป็น **Public** เพื่อใช้งานรันฟรีได้ไม่จำกัดเวลา

3. **เกิด `KeyError` หรือแจ้งเตือนว่าไม่พบ Environment Variable**
   - ตรวจสอบชื่อ Secrets ใน GitHub Secrets ว่าตั้งชื่อตรงกับคีย์ที่กำหนดใน `monitor.yml` ทุกตัวอักขระหรือไม่

4. **YouTube API Error (403 / Quota Exceeded)**
   - ตรวจสอบว่าได้กดเปิดใช้งาน **YouTube Data API v3** ใน Google Cloud Console แล้วหรือยัง
   - ตรวจสอบว่า API Key ยังใช้งานได้ปกติ และโควต้าประจำวัน (10,000 Units) ไม่ได้หมดลง

5. **ดึงข้อมูลช่อง YouTube ไม่สำเร็จ (Channel Fetch Error)**
   - ตรวจสอบ `id` ของช่องใน `config.json` ว่าขึ้นต้นด้วย `UC...` เสมอ (ห้ามใช้ Handle เช่น `@ChannelName` หรือ Custom URL)

6. **ระบบไม่ส่งแจ้งเตือน Error บน Discord ซ้ำๆ**
   - ระบบมีระบบ **6-Hour Anti-Spam Cooldown** สำหรับ Error ข้อความเดิม เพื่อป้องกันสปัมข้อความรบกวนใน Discord ทุก 5 นาที สามารถเข้าไปตรวจสอบรายละเอียดการทำงานจริงได้ที่แท็บ Actions บน GitHub
