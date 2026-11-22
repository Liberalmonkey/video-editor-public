---
name: teleprompter
description: Seslendirme için yerel teleprompter'ı açar. "teleprompter aç", "metni okuyacağım", "seslendirme kaydedeceğim" dendiğinde kullan.
---

# Teleprompter

Arka planda başlat, `--lan` kullanma:

```
EYELINE_DATA=Projeler/inputs/_teleprompter .venv/Scripts/python library/vendor/eyeline-teleprompter/server.py
```

Kullanıcıya `http://localhost:5317` adresini söyle. Metni Chrome ya da Edge'de kullansın; ses takibi tarayıcının konuşma tanıma servisini kullanır. Kayıt bitince dosya `Projeler/inputs/<stüdyo>/<proje>/` klasörüne konur.
