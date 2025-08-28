#!/bin/bash

# MSR USB Relay için tam kurulum scripti

echo "🚀 MSR USB Relay kurulumu başlıyor..."

# USB cihazlarını kontrol et
echo "USB cihazları kontrol ediliyor..."
lsusb | grep -E "(5131|1a86)" && echo "✅ Cihazlar tespit edildi" || echo "❓ Cihazlar bulunamadı"

# Udev kuralları oluştur
echo "Udev kuralları ekleniyor..."
sudo tee /etc/udev/rules.d/99-msr-relay.rules > /dev/null << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="5131", ATTR{idProduct}=="2007", MODE="0666", GROUP="plugdev", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{idProduct}=="7523", MODE="0666", GROUP="plugdev", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="5131", MODE="0666", GROUP="plugdev", TAG+="uaccess"
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout"
EOF

# Kullanıcı yetkileri
echo "Kullanıcı yetkileri ayarlanıyor..."
sudo usermod -a -G plugdev,dialout $USER

# Udev kurallarını yenile
sudo udevadm control --reload-rules
sudo udevadm trigger

# pyserial ve pyusb paketlerini güncelle
echo "Python paketleri güncelleniyor: pyserial ve pyusb..."
if pip3 install --upgrade pyserial pyusb; then
    echo "✅ pyserial ve pyusb başarıyla yüklendi/güncellendi."
else
    echo "❌ pyserial ve pyusb yüklenirken hata oluştu!"
fi

echo ""
echo "✅ KURULUM TAMAMLANDI!"
echo "====================="
echo "📋 Kontrol komutları:"
echo "  lsusb | grep -E '(5131|1a86)'"
echo ""
echo "🔄 USB cihazını çıkarıp takın ve terminali yeniden açın"