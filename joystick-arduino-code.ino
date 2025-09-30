const int joyXPin = A1;
const int joyYPin = A0;
const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT_PULLUP);
}

void loop() {
  int joyX = analogRead(joyXPin);
  int joyY = analogRead(joyYPin);
  int buttonState = digitalRead(buttonPin);
  
  Serial.print(joyX);
  Serial.print(",");
  Serial.print(joyY);
  Serial.print(",");
  Serial.println(buttonState);
  delay(100);
}
