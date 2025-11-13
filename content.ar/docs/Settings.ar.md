---
title: "إعدادات الطرف الرئيسي"
weight: 4
---
{{< hint info >}}
<strong>عند تثبيت التطبيق</strong>، ستكون معظم الإعدادات متاحة بشكل <strong>ديناميكي</strong>. <strong>عليك فقط أن تتعلم المزيد</strong> لضمان سير كل شيء بسلاسة.
{{< /hint >}}

إعدادات الطرف الرئيسي (Party Master Settings) → جدول <strong>أنواع الأطراف</strong> (Party Types)

سيتم تعيين جميع أنواع الأطراف من أنواع الأطراف في ERPNext هنا.

| العمود | المعنى |
| :--- | :--- |
| <strong>إلزامي (Mandatory)</strong> | يصبح <strong>الطرف الرئيسي</strong> <strong>مطلوبًا</strong> عند حفظ عميل/مورد/... |
| <strong>السماح بأطراف متعددة (Allow Multi Party)</strong> | يمكن لأكثر من عميل (أو مورد) الإشارة إلى <strong>نفس الطرف الرئيسي</strong> – يتم التمييز بينها بواسطة <strong>حقل القاعدة (Rule Field)</strong> (على سبيل المثال: `default_currency`) |

---

## 8.2 أنواع مستندات المعاملات (Transaction doctypes)

إعدادات الطرف الرئيسي (Party Master Settings) → جدول <strong>أنواع المستندات</strong> (Document Types)

أضف أي <strong>نوع مستند مخصص (custom doctype)</strong> يحتوي على <strong>رابط (Link)</strong> أو <strong>رابط ديناميكي (Dynamic Link)</strong> إلى طرف.
سيقوم النظام تلقائيًا بإدراج حقل `party_master` والحفاظ على مزامنته.
<strong>الجداول الفرعية مدعومة</strong> – قم بتعيين نوع المستند الأصلي (Parent Doctype) (على سبيل المثال: “Journal Entry Account” الأصل = “Journal Entry”).
