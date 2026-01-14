# Pitch Script: Sentix - The Truth Layer for Crypto Markets

**Intro**
"ในห้องนี้มีใครเทรดคริปโตบ้างครับ...?" (Pause for hands)
"แล้วมีใครเคยเสียเงิน... เพราะ 'ตามข่าวไม่ทัน' หรือ 'โดนข่าวหลอก' บ้างไหมครับ?"

---

### **Problem**
**"The Speed & Verification Gap"**

*   **ปัญหาที่ 1: ข่าวปลอมทำลายพอร์ต (Market Impact)**
    *   รู้ไหมครับว่าเมื่อเดือนมกราคม 2024 เหตุการณ์ **"SEC Fake Tweet"** ที่ทวีตว่า Bitcoin ETF ผ่านการอนุมัติแล้ว (ทั้งที่ยังไม่ผ่าน) ทำให้ตลาด Swing รุนแรง
    *   **สถิติ:** ภายในเวลาไม่กี่นาที มีคนโดนล้างพอร์ต (Liquidations) รวมมูลค่ากว่า **$90 ล้านดอลลาร์** (ประมาณ 3,000 ล้านบาท) เพียงเพราะเชื่อข่าวปลอมทวีตเดียว
        *   *(Source: CoinGlass / Reuters reports on Jan 9, 2024 SEC X account hack)*
    *   **User Pain Point:** นักเทรดรายย่อย 90% เสียเงินไม่ใช่เพราะเทรดไม่เก่ง แต่เพราะเข้าซื้อตอน "ดอย" เพราะเห็นข่าวช้า หรือ Panic Sell เพราะข่าว FUD (Fake News)

*   **ปัญหาที่ 2: ช้ากว่าก็แพ้ (Latency)**
    *   คนทั่วไปอ่านข่าวจาก Facebook/Line ซึ่งช้ากว่าตลาดจริง 15-30 นาที
    *   วาฬและบอทรู้ข่าวก่อนเราเสมอ ถ้าเราไม่มีเครื่องมือ เราก็เป็นได้แค่ "สภาพคล่อง" ให้คนอื่น

*   **ถ้าไม่แก้:** เราจะยังคงเป็น "แมงเม่า" ที่ซื้อข่าวร้าย ขายข่าวดี และตลาดคริปโตจะไม่มีวันเป็น Mainstream ได้ถ้าเต็มไปด้วยข่าวลวง

---

### **Solution**

*   **One-Liner:** "Sentix คือ AI Intelligence Agent ที่ไม่ได้แค่ 'อ่านข่าว' แต่ทำหน้าที่ 'สืบสวนและยืนยันข่าว' ให้คุณก่อนกราฟจะวิ่ง"
*   **How it works:**
    *   Sentix จับสัญญาณข่าวจากทั่วโลก (RSS & Social)
    *   แต่จุดเด่นคือ **"Verification Layer"**: ก่อนโพสต์ทุกครั้ง AI จะเช็คกราฟราคา (Price Action) และเช็คข้อมูลบน Blockchain (On-Chain Data) ว่าเงินไหลเข้าจริงไหม?
    *   **User Value:** เปลี่ยนจาก "เดาข่าว" เป็น "รู้ความจริง" ภายใน 1 นาที

*   **Differentiation:**
    *   Bot ทั่วไป: รีทวีตทุกอย่างที่เห็น (ขยะ = ขยะ)
    *   **Sentix:** กรองข่าวลวงด้วย On-Chain Data ถ้ากราฟไม่วิ่ง วาฬไม่ขยับ Sentix จะไม่โพสต์ หรือจะเตือนว่าเป็นข่าวปลอม

---

### **Technology**

**Pipeline การทำงาน (The Truth Pipeline):**

1.  **Ingestion (หู):** ดึงข้อมูลดิบจาก Top Tier RSS (CoinDesk, WatcherGuru) *โดยตัดการพึ่งพา Twitter Ingestion API เพื่อแก้ปัญหา Rate Limit 100%*
2.  **Resolution (สมองซีกซ้าย):** ใช้ Algorithm จัดกลุ่มข่าวที่เหมือนกัน (Clustering) เพื่อดูว่าแหล่งข่าวพูดตรงกันกี่เจ้า (Consensus Verification)
3.  **Verification (ตาส่อง):**
    *   ยิง API ไปเช็คราคา (CoinGecko)
    *   เช็ค Mempool Transaction (Blockchain.info) ว่ามีวาฬโอนเงินจริงไหม
4.  **Analysis (สมองซีกขวา):** ใช้ **Google Gemini 3 Flash** (รุ่นใหม่ล่าสุดที่เร็วที่สุด) วิเคราะห์ความสัมพันธ์ และเขียนสรุป
5.  **Visualization (ปาก):** ใช้ Playwright บินไปแคปภาพกราฟ TradingView แบบ Real-time และโพสต์ลง X

**Stakeholders:**
*   **Trader (User):** รอรับ Signal ที่แม่นยำ
*   **Developer/Admin:** คนคุม System ผ่าน Dashboard
*   **Market Data Providers:** CoinGecko/Exchange ที่เราดึงข้อมูลมา Verify

---

### **Demo / Storyboard**

*(เนื่องจากเป็น Presentation สด ให้เล่าประกอบภาพ Slide)*

*   **Scene 1: The Dashboard (Control Room)**
    *   "นี่คือหน้าบ้านของระบบครับ แสดงสถานะ Bot แบบ Real-time เราจะเห็นว่าตอนนี้ Bot กำลังจับตาดู Bitcoin อยู่" (โชว์ภาพหน้าจอ Dashboard สีดำ มีกราฟวิ่ง)

*   **Scene 2: The Audit Log (The "Trust" Feature)**
    *   "ไฮไลท์คือหน้านี้ครับ **Audit Log**... เราสามารถดูย้อนหลังได้ว่า ทำไม AI ถึงตัดสินใจโพสต์ หรือ ไม่โพสต์"
    *   "เช่นเคสนี้: มีข่าวลือว่า SEC แบนเหรียญ X... แต่ AI ไปเช็ค On-Chain แล้วไม่เจอ Transaction ผิดปกติ มันเลยแปะป้ายว่า **UNVERIFIED** และไม่ส่งต่อข่าวลวงนี้ให้ User"

*   **Scene 3: The Result (On X/Twitter)**
    *   "และนี่คือผลลัพธ์ที่ User เห็น... ทวีตสรุปสั้นๆ พร้อม **Confidence Score** (ความมั่นใจ) และรูปกราฟราคา ณ วินาทีนั้น... จบ ครบ ในโพสต์เดียว"

---

### **Impact & Value**

*   **ต่อ User (นักเทรด):**
    *   ประหยัดเวลาอ่านข่าววันละ 2-3 ชั่วโมง เหลือเพียงอ่านสรุปที่ Verify แล้ว
    *   ลดโอกาสขาดทุนจากการ Panic ตามข่าวปลอม (Capital Preservation)
*   **ต่อ Business:**
    *   สามารถขาย API ข่าวที่ Clean แล้วให้กับ Platform เทรดอื่น หรือทำ Paid Group
*   **ต่ออุตสาหกรรม:**
    *   สร้าง Standard ใหม่ให้วงการข่าวคริปโต ว่า "ข่าวที่ดีต้องมี Data รองรับ" ลดความผันผวนของตลาดโดยรวม

---

### **Challenges & Learnings**

*   **1. ปัญหา Hallucination (AI มั่ว):**
    *   *Challenge:* ช่วงแรก AI ชอบแต่งเรื่องเองเพื่อเอาใจเรา
    *   *Fix:* เราสร้างระบบ **RAG Memory** และ **Critic Loop** คือมี AI อีกตัวทำหน้าที่เป็น " บ.ก." คอยตรวจสอบ Fact ก่อนโพสต์เสมอ
*   **2. ปัญหา External API Limits:**
    *   *Challenge:* Twitter API ราคาแพงและจำกัดการดึงข้อมูล
    *   *Fix:* เราเปลี่ยนโครงสร้างไปใช้ RSS Feed เป็นหลัก และใช้ Twitter เพื่อการโพสต์เท่านั้น ทำให้ระบบเสถียรและ Cost ต่ำลงมาก
*   **3. ปัญหา Latency:**
    *   *Challenge:* การ Verify ข้อมูลใช้เวลานาน
    *   *Fix:* ใช้โมเดล **Gemini Flash** ที่เร็วที่สุด และเขียนโค้ดแบบ Asynchronous ทำให้ Process ทั้งหมดจบใน < 45 วินาที

---

### **Future Plan**

*   **Phase 1: The Trust Builder (Current)**
    *   Focus: สร้างฐานผู้ติดตาม และเก็บ Data ความแม่นยำของข่าว
    *   **Cost:** ~$5/เดือน
        *   *Google Cloud Run (Free Tier for small usage, scaling to ~$5)*
        *   *Gemini API (Free Tier or ~$0.07/1M tokens)*
    *   **Revenue:** $0 (Growth Stage)

*   **Phase 2: The Signal Provider (Next 6 Months)**
    *   Feature: เพิ่มเหรียญ Altcoins และแจ้งเตือนผ่าน Line/Discord ส่วนตัว
    *   **Cost:** ~$100/เดือน
        *   *Cloud SQL DB Upgrade*
        *   *Server Scaling for 1000+ concurrent users*
    *   **Revenue:** ~$1,000/เดือน
        *   *Subscription Model: 200 บาท/เดือน x 150 คน (Conversion rate 1-2% จาก Follower หลักหมื่น)*

*   **Phase 3: The Trading Terminal (Long Term)**
    *   Feature: เชื่อมต่อ API สั่งเทรดตามข่าวได้เลย (Auto-Trade)
    *   **Cost:** ~$1,000+/เดือน
        *   *High-Frequency Server & Dedicated Nodes*
    *   **Revenue:** ~$10,000+/เดือน
        *   *Profit Sharing Model / B2B Data Licensing ให้เว็บข่าวอื่น*

---

### **Conclusion**

"ในโลกการเงิน... 'ข้อมูล' คืออาวุธ แต่ 'ข้อมูลที่ถูกต้อง' คือเกราะป้องกัน"

**"Sentix: Don't just read the news. Verify it."**
(ไม่ต้องเชื่อแค่ข่าว... แต่จงเชื่อข้อมูลที่พิสูจน์แล้ว)

ขอบคุณครับ
