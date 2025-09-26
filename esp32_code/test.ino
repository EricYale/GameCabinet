void setup() {
  Serial.begin(115200);
  pinMode(5, INPUT_PULLUP);
  pinMode(18, INPUT_PULLUP);
  pinMode(15, INPUT_PULLUP);
  pinMode(2, INPUT_PULLUP);
}

void loop() {
  Serial.print(analogRead(34));
  Serial.print("/");
  Serial.print(analogRead(35));
  Serial.print("/");
  Serial.print(analogRead(33));
  Serial.print("/");
  Serial.print(analogRead(25));
  Serial.print("/");
  Serial.print(digitalRead(5));
  Serial.print("/");
  Serial.print(digitalRead(18));
  Serial.print("/");
  Serial.print(digitalRead(15));
  Serial.print("/");
  Serial.print(digitalRead(2));
  Serial.println("");
}