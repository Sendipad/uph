---
draft: false
title: "المورّد يصدر لك فاتورة بعملات يورو و دولار و درهم"
weight: 20
tags : [
    "usage",
    "case",
    "example",
    "howto",
]
date : "2025-04-02"
categories : [
    "Usage Cases",
    "examples",
]
menu : 
  main: 
    parent: Blog
---

{{< hint info >}} 
المورّد <strong>Alpha Export LLC</strong> يصدر لك فواتير بعملتي <strong>EUR</strong> و<strong>USD</strong>.
{{< /hint >}} 

{{% steps %}}
1. ## إعدادات سجل الأطراف → نوع الطرف (الجدول)
   <strong>Supplier</strong> → <strong>Allow Multi Party</strong> = ✅، <strong>Rule Field</strong> = `default_currency` 

2. ## انتقل إلى Party Master، سجل Alpha Export LLC
   أنشئ طرفًا جديدًا (الافتراضي Supplier) → <strong>العملة</strong> = <strong>EUR</strong> → <strong>حفظ</strong>.  
   أعد إنشاء طرف آخر لنفس المورّد → <strong>العملة</strong> = <strong>USD</strong> → <strong>حفظ</strong>.

3. ## انتقل إلى فاتورة الشراء (Purchase Invoice)
   اختر <strong>Alpha Export USD</strong> → <strong>العملة</strong> = <strong>USD</strong> → <strong>اعتماد</strong>.

4. ## كشف حساب الطرف (Party Account Statement)
   يعرض الأرصدة بعملتي <strong>EUR</strong> و<strong>USD</strong> جنبًا إلى جنب.
{{% /steps %}}
