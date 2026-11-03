# YouTube Discord Monitor

ระบบแจ้งเตือนคลิปวิดีโอใหม่และการไลฟ์สดจากช่อง YouTube ไปยัง Discord โดยอัตโนมัติ ผ่าน Discord Webhook และ GitHub Actions

ระบบจะตรวจสอบช่อง YouTube ที่กำหนดไว้ทุก ๆ 5 นาที โดยไม่จำเป็นต้องเปิดคอมพิวเตอร์ทิ้งไว้

## ✨ ความสามารถของระบบ

- ตรวจสอบคลิปวิดีโอใหม่จากช่อง YouTube ที่กำหนด
- ตรวจสอบการไลฟ์สด (Live) และแจ้งเตือนเมื่อเริ่มไลฟ์
- รองรับ YouTube Shorts
- สามารถเพิ่มช่อง YouTube ได้หลายช่อง
- แบ่งกลุ่มช่อง YouTube เพื่อส่งการแจ้งเตือนไปยัง Discord คนละห้องได้
- ทำงานอัตโนมัติผ่าน GitHub Actions ทุก 5 นาที
- บันทึกประวัติคลิปที่เคยตรวจสอบแล้ว เพื่อป้องกันการแจ้งเตือนซ้ำ

## 📁 ไฟล์สำคัญ

| ไฟล์ | หน้าที่ |
|---|---|
| `monitor.py` | โค้ดหลักสำหรับตรวจสอบ YouTube และส่งแจ้งเตือน |
| `config.json` | ตั้งค่าช่อง YouTube และกลุ่ม Discord |
| `state.json` | เก็บประวัติคลิปและสถานะการแจ้งเตือน |
| `requirements.txt` | รายการ Python Libraries ที่จำเป็น |
| `.github/workflows/` | ตั้งค่าการทำงานอัตโนมัติของ GitHub Actions |

## ⚙️ วิธีติดตั้งและตั้งค่า

### 1. เตรียมสิ่งที่จำเป็น

- GitHub Account
- YouTube Data API v3 API Key
- Discord Webhook URL
- Repository สำหรับเก็บโปรเจกต์นี้

### 2. ตั้งค่า YouTube API

1. เข้าไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้าง Project ใหม่ หรือเลือก Project ที่มีอยู่
3. เปิดใช้งาน **YouTube Data API v3**
4. สร้าง API Key
5. คัดลอก API Key เก็บไว้

### 3. สร้าง Discord Webhook

ทำตามขั้นตอนนี้ใน Discord:

1. เข้าไปที่ Server ที่ต้องการรับการแจ้งเตือน
2. เลือกห้องข้อความที่ต้องการ
3. เข้าไปที่ Edit Channel
4. เลือก Integrations
5. เลือก Webhooks
6. กด New Webhook
7. คัดลอก Webhook URL เก็บไว้

หากต้องการแยกการแจ้งเตือนเป็น 2 กลุ่ม ให้สร้าง Webhook สำหรับแต่ละห้อง

### 4. ตั้งค่า GitHub Secrets

เข้าไปที่ Repository บน GitHub แล้วเลือก:

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

เพิ่ม Secrets ทั้ง 3 รายการดังนี้:

| Secret Name | Value |
|---|---|
| `YOUTUBE_API_KEY` | YouTube API Key |
| `DISCORD_WEBHOOK_A` | Discord Webhook ของกลุ่ม A |
| `DISCORD_WEBHOOK_B` | Discord Webhook ของกลุ่ม B |

**หมายเหตุ:** ห้ามนำ API Key หรือ Webhook URL ไปใส่ไว้ในไฟล์โค้ดที่เป็นสาธารณะ

## 📝 การเพิ่มช่อง YouTube

เปิดไฟล์ `config.json` แล้วแก้ไขข้อมูลช่อง YouTube ที่ต้องการติดตาม

ตัวอย่าง:

```json
{
  "check_interval_minutes": 5,
  "groups": {
    "A": {
      "webhook_env": "DISCORD_WEBHOOK_A"
    },
    "B": {
      "webhook_env": "DISCORD_WEBHOOK_B"
    }
  },
  "channels": [
    {
      "name": "Channel 1",
      "id": "YOUR_CHANNEL_ID_1",
      "group": "A"
    },
    {
      "name": "Channel 2",
      "id": "YOUR_CHANNEL_ID_2",
      "group": "B"
    }
  ]
}
```

วิธีเพิ่มช่องใหม่:

1. คัดลอก Channel ID จากช่อง YouTube ที่ต้องการติดตาม
->โดยเข้าไปที่หน้า Youtube Channel จากนั้นคลิ๊กขวา แล้วกด View page source แล้วกด Ctrl+F จากนั้นป้อน channel_id แล้ว copy ส่วนที่ขึ้นต้นด้วย UR มาใช้
2. เพิ่มข้อมูลช่องลงในส่วน `channels`
3. กำหนด `name` ตามใจฉัน
4. กำหนด `id` เป็น Channel ID
5. กำหนด `group` เป็น `A` หรือ `B` หรืออื่นๆตามห้อง Discord ที่ต้องการรับแจ้งเตือน

ตัวอย่าง:

```json
{
  "name": "Example Channel",
  "id": "UCxxxxxxxxxxxxxxxx",
  "group": "A"
}
```

## 🚀 วิธีเริ่มใช้งาน

1. ตรวจสอบว่าได้ตั้งค่า GitHub Secrets และ `config.json` เรียบร้อยแล้ว
2. เข้าไปที่ Repository บน GitHub
3. เลือกแท็บ **Actions**
4. เลือก Workflow ชื่อ **YouTube Discord Monitor**
5. กด **Run workflow** เพื่อทดสอบการทำงาน

เมื่อเริ่มทำงานครั้งแรก ระบบจะบันทึกคลิปล่าสุดของแต่ละช่องไว้เป็นประวัติ โดยจะไม่ส่งแจ้งเตือนคลิปเก่าที่มีอยู่ก่อนแล้ว

หลังจากนั้นระบบจะตรวจสอบคลิปใหม่และ Live โดยอัตโนมัติทุก ๆ 5 นาที

## 🔔 รูปแบบการแจ้งเตือน(ของฉันเองจ้า)

**เมื่อมีคลิปใหม่**

FEDDING TIME🍗🍗 Unstable SMP NEW VIDEO!!

ตามด้วยลิงก์ YouTube ของคลิป

**เมื่อมีการไลฟ์สด**

NO WAY?? Unstable SMP MEMBER IS LIVE!!

ตามด้วยลิงก์ YouTube ของ Live

## 📌 การทำงานของระบบ

- GitHub Actions จะเรียกใช้งาน `monitor.py` ทุก ๆ 5 นาที
- ระบบใช้ YouTube Data API v3 เพื่อตรวจสอบข้อมูลช่องและวิดีโอ
- เมื่อพบคลิปใหม่หรือ Live ระบบจะส่งข้อความไปยัง Discord Webhook ตามกลุ่มที่กำหนด
- ระบบบันทึกประวัติลงใน `state.json`
- GitHub Actions จะอัปเดต `state.json` กลับไปยัง Repository เพื่อเก็บสถานะการตรวจสอบครั้งล่าสุด

## 🛠️ การแก้ไขและอัปเดตโปรเจกต์

หากต้องการแก้ไขโค้ดหรือเพิ่มช่อง YouTube สามารถทำผ่าน GitHub Codespaces ได้

หลังจากแก้ไขเสร็จแล้ว ใช้คำสั่ง:

```bash
git add .
git commit -m "update monitor"
git push origin main
```

เมื่อ Push สำเร็จ GitHub จะบันทึกการเปลี่ยนแปลง และระบบจะใช้โค้ดเวอร์ชันใหม่ในการทำงานครั้งถัดไป

---

**หมายเหตุ:** หากต้องการให้ระบบทำงานได้อย่างต่อเนื่อง ต้องเปิดใช้งาน GitHub Actions และตรวจสอบว่า API Key กับ Discord Webhook ยังใช้งานได้ตามปกติ