# Sơ đồ nối Raspberry Pi – L298N – động cơ DC – LED

Sơ đồ dành cho Raspberry Pi 4 có đầu GPIO 40 chân và module L298N có các đầu `ENA`, `IN1`, `IN2`, `OUT1`, `OUT2`, `Vs/+12V`, `GND`, `5V`, jumper `5V-EN`. Các số GPIO khớp `config.py` của bài `weather_v2`.

![Sơ đồ nối mạch chi tiết](assets/wiring-l298n.png)

[Bản SVG để phóng to hoặc in](assets/wiring-l298n.svg).

Vị trí đầu nối trong hình được bố trí theo chức năng để dễ đọc. Khi nối module thật, đối chiếu **nhãn in trên PCB**, không suy ra vị trí chân từ hình. Chấm tròn đặc trên đường dây biểu thị điểm nối chung; hai dây cắt nhau không có chấm không nối điện với nhau.

## Linh kiện

- Raspberry Pi 4, nguồn cấp Pi qua USB-C.
- Module L298N có tản nhiệt, diode bảo vệ và jumper nguồn logic.
- Một động cơ DC chổi than và nguồn DC riêng phù hợp với động cơ/module.
- Một LED, điện trở **330 Ω** (có thể dùng 220–330 Ω).
- Dây nối, breadboard hoặc đầu nối để gom GND chung.

## Cấu hình hai jumper trước khi cấp nguồn

Sơ đồ chọn cấp **5V logic từ Raspberry Pi**, còn động cơ dùng nguồn riêng. [Tài liệu module Handson MDU-1049](https://www.handsontec.com/dataspecs/L298N%20Motor%20Driver.pdf) trình bày cách cấp 5V ngoài với jumper nguồn logic được tháo.

| Jumper trên L298N | Thao tác | Mục đích |
| --- | --- | --- |
| **ENA** | **Tháo** | GPIO18 gửi PWM để thay đổi tốc độ kênh A |
| **5V-EN / 5V Enable** | **Tháo** | Chân `5V` nhận nguồn logic 5V ngoài từ Pi |
| ENB | Kênh B không sử dụng | Không nối GPIO hay động cơ vào kênh B trong bài này |

Hai jumper ENA và 5V-EN có chức năng riêng. Khi tháo jumper ENA, nối GPIO18 vào **chân tín hiệu ENA**, không nối vào chân 5V nằm cạnh nó trên cặp chân cắm jumper. Khi tháo jumper 5V-EN, không nối GPIO vào hai chân cắm jumper đó.

## Bảng nối từng dây

**Tắt nguồn Pi và nguồn động cơ trước khi đấu dây.** GPIO của Pi dùng tín hiệu 3,3V; chân `5V` vật lý số 2 là chân cấp nguồn, khác với GPIO. [Tài liệu GPIO Raspberry Pi](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header)

| # | Điểm đầu | Điểm cuối | Chức năng |
| --- | --- | --- | --- |
| 1 | Pi **GPIO27 – chân vật lý 13** | L298N **IN1** | Điều khiển chiều quay |
| 2 | Pi **GPIO22 – chân vật lý 15** | L298N **IN2** | Điều khiển chiều quay |
| 3 | Pi **GPIO18 – chân vật lý 12** | L298N **ENA** sau khi tháo jumper | Điều chỉnh tốc độ bằng PWM |
| 4 | Pi **5V – chân vật lý 2** | L298N **5V**, sau khi tháo jumper 5V-EN | Cấp nguồn logic cho driver |
| 5 | Pi **GND – chân vật lý 6** | Điểm **GND chung** | Mass của Pi |
| 6 | L298N **GND** | Điểm **GND chung** | Mass của driver |
| 7 | Cực **âm (−)** nguồn động cơ | Điểm **GND chung** | Mass của nguồn công suất |
| 8 | Cực **dương (+)** nguồn động cơ | L298N **Vs / +12V / Motor Supply** | Cấp nguồn công suất cho động cơ |
| 9 | L298N **OUT1** | Dây thứ nhất của động cơ | Đầu ra cầu H |
| 10 | L298N **OUT2** | Dây thứ hai của động cơ | Đầu ra cầu H |
| 11 | Pi **GPIO17 – chân vật lý 11** | Một đầu điện trở **330 Ω** | Tín hiệu bật/tắt LED |
| 12 | Đầu còn lại điện trở | **Anode A (+), chân dài LED** | Hạn dòng LED |
| 13 | **Cathode K (−), chân ngắn LED** | Điểm **GND chung** | Đường về của LED |

GND chung có thể là một thanh GND trên breadboard: nối bốn dây từ Pi, driver, nguồn động cơ và cathode LED vào cùng thanh đó. Nếu thanh nguồn breadboard bị ngắt ở giữa, dùng dây nối hai đoạn để chúng thông nhau.

## Các chân trên L298N có ý nghĩa gì?

| Nhãn module | Ý nghĩa trong sơ đồ |
| --- | --- |
| **IN1, IN2** | Hai tín hiệu xác định chiều dòng qua động cơ kênh A |
| **ENA** | Cho phép kênh A hoạt động; PWM tại đây điều chỉnh mức công suất |
| **OUT1, OUT2** | Hai đầu nối ra động cơ kênh A |
| **Vs / +12V** | Đầu nguồn công suất của động cơ; giá trị cấp thực tế tùy động cơ và module |
| **5V** | Nguồn logic 5V vào module trong cấu hình đã tháo 5V-EN |
| **GND** | Mốc 0V chung của toàn mạch |
| **IN3, IN4, ENB, OUT3, OUT4** | Kênh B, không dùng trong bài này |

L298 chấp nhận mức HIGH từ 2,3V trở lên, nên tín hiệu 3,3V của Pi điều khiển trực tiếp các đầu IN1/IN2/ENA. Nguồn logic của L298 vẫn cần 5V riêng như sơ đồ. [Datasheet ST L298, bảng thông số điện](https://www.st.com/resource/en/datasheet/l298.pdf)

Đầu ghi `+12V` trên nhiều module là đầu nguồn **Vs**, không có nghĩa mọi động cơ đều phải cấp 12V. Ví dụ với động cơ định mức 12V, dùng nguồn 12V phù hợp về dòng; với động cơ điện áp khác, chọn nguồn tương ứng và kiểm tra giới hạn module. L298 có sụt áp qua cầu H, nên điện áp thực tế tới động cơ thấp hơn nguồn; nguồn cũng cần đủ dòng khởi động của động cơ. [Datasheet ST L298](https://www.st.com/resource/en/datasheet/l298.pdf)

Trong phương án này, Pi được cấp qua USB-C và cấp một phần công suất nhỏ cho logic L298N. **Không cấp động cơ từ chân 5V của Pi**, không nối nguồn động cơ vào GPIO, và không dùng đầu 5V của module để cấp ngược cho Pi. Nếu để jumper 5V-EN cắm, đầu 5V có thể trở thành ngõ ra của bộ ổn áp trên module; vì vậy chỉ đấu dây Pi 5V → module 5V sau khi đã tháo jumper nguồn logic theo đúng loại module.

## Tín hiệu ứng với yêu cầu bài

| Trạng thái | IN1 / GPIO27 | IN2 / GPIO22 | ENA / GPIO18 |
| --- | --- | --- | --- |
| **t ≥ 30°C** | HIGH | LOW | PWM **100%**: quay thuận, nhanh |
| **t < 30°C** | LOW | HIGH | PWM **40%**: quay nghịch, chậm |
| API lỗi / thoát chương trình | LOW | LOW | **0%**: ngắt công suất, động cơ thả trôi tới khi dừng |

Chiều thuận/nghịch được quy ước theo thứ tự OUT1/OUT2. Nếu chiều thực tế ngược mong muốn, tắt nguồn rồi đổi hai dây động cơ. Chương trình ngắt ENA và chờ trước khi đổi chiều. Bảng trạng thái cầu H theo [datasheet ST L298](https://www.st.com/resource/en/datasheet/l298.pdf).

GPIO17 HIGH làm LED sáng khi xác suất mưa **> 70%**; GPIO17 LOW làm LED tắt khi xác suất **≤ 70%**. Động cơ và LED được điều khiển độc lập.

## Trình tự chạy sau khi nối dây

1. Kiểm tra jumper ENA và 5V-EN đều đã tháo; kiểm tra không nhầm đầu Vs với đầu 5V.
2. Kiểm tra GND Pi, GND L298N, cực âm nguồn động cơ và cathode LED đã nối chung.
3. Cấp nguồn Pi qua USB-C; nguồn động cơ vẫn tắt. L298N nhận 5V logic từ Pi.
4. Trong `weather_v2`, nạp key và chạy `python app.py`. Khi thấy lời nhắc nhập thành phố, GPIO đã khởi tạo với ENA ở mức tắt.
5. Cấp nguồn động cơ, rồi nhập thành phố để lấy dữ liệu và điều khiển.
6. Khi kết thúc, gõ `q` hoặc nhấn Ctrl+C; tắt nguồn động cơ trước khi đổi dây hoặc tắt Pi.

Sơ đồ đã đối chiếu chân Pi với dữ liệu pinout của gpiozero và các hằng trong `config.py`. Chưa kiểm tra trên phần cứng thật.
