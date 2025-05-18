## **Hướng dẫn Sửa lỗi và Tối ưu hóa Chức năng Xuất CSV**

## Vấn đề chính với chức năng xuất CSV hiện tại nằm ở việc hàm JavaScript không nhắm đúng vào các nút bấm và thiếu các thuộc tính dữ liệu cần thiết để xác định bảng nào cần xuất.

### **1. Phân tích Lỗi Hiện tại trong** `data.html`

Trong file `templates/data.html`, có hai loại nút xuất CSV:1) ******Nút "Export CSV" chung:******

       <button id="exportCsvBtn" class="btn btn-sm btn-outline-secondary">
           <i class="fas fa-file-export me-1"></i>Export CSV
       </button>

   Nút này dùng để xuất dữ liệu từ bảng "All Records" (`#all-data-table`).

2) ******Nút "Export Data" cho từng thiết bị:******

       <button class="btn btn-sm btn-outline-primary device-export" data-device-id="{{ device_id }}">
           <i class="fas fa-download me-1"></i>Export Data
       </button>

   Nút này nằm trong mỗi thẻ thiết bị và dùng để xuất dữ liệu của thiết bị đó.Hàm `setupCsvExport()` trong `data.html` có các vấn đề sau:* ******Sai selector:****** `$('.export-csv-btn').on('click', ...)` không khớp với ID `exportCsvBtn` của nút chung.

* ******Thiếu** `data-target` **và** `data-filename`**:****** Code cố gắng đọc `$(this).data('target')` và `$(this).data('filename')` từ nút bấm, nhưng các thuộc tính này không được định nghĩa trên nút `exportCsvBtn`.

* ******Chưa xử lý cho** `.device-export`**:****** Hàm hiện tại không được thiết kế để xử lý các nút export của từng thiết bị.
------------------------------------------------------------------------------------------------------------------------------

### **2. Giải pháp Khắc phục và Tối ưu hóa**

## Chúng ta sẽ chia thành hai phần: sửa nút export chung và triển khai nút export cho từng thiết bị.

#### **2.1. Sửa lỗi cho Nút "Export CSV" Chung (**`#exportCsvBtn`**)**

Nút này sẽ dùng để xuất dữ liệu từ bảng `#all-data-table`.******Các bước:******1) ******Cập nhật hàm** `setupCsvExport` **trong** `data.html`**:******

   - Thay đổi selector để nhắm đúng vào `#exportCsvBtn`.

   - Gán cố định `targetTable` là `'#all-data-table'`.

   - Đặt tên file mặc định, ví dụ `all_records_export.csv`.******Code mẫu cập nhật cho** `setupCsvExport` **trong** `templates/data.html` **(phần** `<script>`**):******            // CSV Export functionality
            function setupCsvExport() {
                // Sửa selector để nhắm đúng ID của nút export chung
                $('#exportCsvBtn').on('click', function() {
                    const targetTable = '#all-data-table'; // Nhắm vào bảng "All Records"
                    const filename = 'all_records_export.csv'; // Đặt tên file mặc định

                    // Kiểm tra xem bảng có tồn tại không
                    if ($(targetTable).length === 0) {
                        alert('Lỗi: Không tìm thấy bảng dữ liệu "All Records".');
                        return;
                    }

                    const rows = [];
                    const headers = [];

                    // Lấy headers từ thead của bảng
                    $(`${targetTable} thead th`).each(function() {
                        headers.push($(this).text().trim());
                    });
                    rows.push(headers);

                    // Lấy dữ liệu từ các hàng trong tbody của bảng
                    // Lưu ý: Đoạn code này sẽ lấy dữ liệu đang hiển thị trên trang (bao gồm cả phân trang của bảng "All Records")
                    // Nếu muốn xuất TOÀN BỘ dữ liệu (kể cả các trang không hiển thị), cần một giải pháp khác,
                    // ví dụ: lấy dữ liệu từ biến `currentAllData` hoặc gọi API để lấy toàn bộ dữ liệu.
                    // Hiện tại, chúng ta sẽ giữ nguyên logic lấy từ DOM để đơn giản.
                    $(`${targetTable} tbody tr`).each(function() {
                        // Chỉ lấy các hàng đang hiển thị (không bị display: none do phân trang)
                        if ($(this).is(":visible")) {
                            const row = [];
                            $(this).find('td').each(function() {
                                let cellText = '';
                                // Đặc biệt xử lý cho cột payload có thể chứa thẻ <pre><code>
                                if ($(this).find('pre code').length > 0) {
                                    cellText = $(this).find('pre code').text().trim();
                                } else {
                                    cellText = $(this).text().trim();
                                }
                                row.push(cellText);
                            });
                            rows.push(row);
                        }
                    });

                    if (rows.length <= 1) { // Chỉ có header
                        alert('Không có dữ liệu để xuất.');
                        return;
                    }

                    // Convert to CSV
                    let csvContent = "data:text/csv;charset=utf-8,";

                    rows.forEach(function(rowArray) {
                        const row = rowArray.map(function(cell) {
                            // Escape quotes và bao trong dấu nháy kép nếu chứa dấu phẩy, nháy kép hoặc xuống dòng
                            let processedCell = cell.toString().replace(/"/g, '""'); // Escape double quotes
                            if (processedCell.includes(',') || processedCell.includes('"') || processedCell.includes('\n')) {
                                processedCell = '"' + processedCell + '"';
                            }
                            return processedCell;
                        }).join(",");
                        csvContent += row + "\r\n";
                    });

                    // Create download link
                    const encodedUri = encodeURI(csvContent);
                    const link = document.createElement("a");
                    link.setAttribute("href", encodedUri);
                    link.setAttribute("download", filename);
                    document.body.appendChild(link); // Required for Firefox
                    link.click();
                    document.body.removeChild(link);
                });
            }

            // Gọi hàm khởi tạo khi tài liệu sẵn sàng
            $(document).ready(function() {
                // ... (các hàm khởi tạo khác như initializeApp)
                setupCsvExport(); // Khởi tạo cho nút export chung
                setupPerDeviceCsvExport(); // Khởi tạo cho các nút export của từng thiết bị (sẽ định nghĩa ở dưới)
            });
---------------

#### **2.2. Triển khai Chức năng Xuất CSV cho Từng Thiết bị (**`.device-export`**)**

Các nút này sẽ xuất dữ liệu từ bảng tương ứng trong thẻ (card) của mỗi thiết bị.******Các bước:******1) ******Tạo hàm** `setupPerDeviceCsvExport` **trong** `data.html`**:******

   - Hàm này sẽ gắn sự kiện `click` cho tất cả các nút có class `.device-export`.

   - Bên trong sự kiện, lấy `deviceId` từ `data-device-id`.

   - Xác định `targetTable` dựa trên `deviceId` (ví dụ: `#device-${deviceId} .data-table`).

   - Tạo tên file động (ví dụ: `device_${deviceId}_data.csv`).

   - Phần logic tạo CSV và tải xuống có thể được tách ra thành một hàm chung để tái sử dụng.******Code mẫu cho hàm** `setupPerDeviceCsvExport` **và hàm helper** `exportTableToCsv` **(thêm vào phần** `<script>` **trong** `templates/data.html`**):******            // Hàm helper chung để tạo và tải CSV từ dữ liệu bảng
            function exportTableDataToCsv(tableSelector, filename) {
                if ($(tableSelector).length === 0) {
                    alert(`Lỗi: Không tìm thấy bảng dữ liệu với selector "${tableSelector}".`);
                    return;
                }

                const rows = [];
                const headers = [];

                // Lấy headers
                $(`${tableSelector} thead th`).each(function() {
                    headers.push($(this).text().trim());
                });
                rows.push(headers);

                // Lấy dữ liệu từ các hàng trong tbody của bảng được chỉ định
                // Đoạn code này sẽ lấy dữ liệu đang hiển thị trên trang cho bảng đó (bao gồm cả phân trang)
                // Nếu muốn xuất TOÀN BỘ dữ liệu của thiết bị, cần lấy từ biến `deviceDataMap.get(deviceId)`
                // và xử lý riêng, không dựa vào DOM.
                // Ví dụ này sẽ lấy từ DOM trước.
                let dataFound = false;
                $(`${tableSelector} tbody tr`).each(function() {
                    if ($(this).is(":visible")) { // Chỉ các hàng đang hiển thị
                        const row = [];
                        $(this).find('td').each(function() {
                            let cellText = '';
                            if ($(this).find('pre code').length > 0) {
                                cellText = $(this).find('pre code').text().trim();
                            } else {
                                cellText = $(this).text().trim();
                            }
                            row.push(cellText);
                        });
                        rows.push(row);
                        dataFound = true;
                    }
                });

                if (!dataFound) {
                    alert('Không có dữ liệu hiển thị để xuất cho thiết bị này.');
                    return;
                }

                // Convert to CSV
                let csvContent = "data:text/csv;charset=utf-8,";
                rows.forEach(function(rowArray) {
                    const row = rowArray.map(function(cell) {
                        let processedCell = cell.toString().replace(/"/g, '""');
                        if (processedCell.includes(',') || processedCell.includes('"') || processedCell.includes('\n')) {
                            processedCell = '"' + processedCell + '"';
                        }
                        return processedCell;
                    }).join(",");
                    csvContent += row + "\r\n";
                });

                // Create download link
                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download", filename);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }

            // Hàm thiết lập export cho từng thiết bị
            function setupPerDeviceCsvExport() {
                // Sử dụng event delegation cho các nút .device-export được thêm động
                $('#device-cards').on('click', '.device-export', function() {
                    const deviceId = $(this).data('device-id');
                    const deviceName = $(this).closest('.device-card').find('.device-title h5').text().trim() || deviceId;
                    
                    // Target bảng dữ liệu cụ thể của thiết bị này
                    // Selector này dựa trên cấu trúc HTML của device card trong data.html
                    const targetTable = `#device-${deviceId} .data-table`;
                    const filename = `device_${deviceName.replace(/\s+/g, '_')}_data.csv`;

                    // Gọi hàm helper để xuất dữ liệu
                    exportTableDataToCsv(targetTable, filename);
                });
            }

            // Trong $(document).ready(function() { ... });
            // đã có:
            // setupCsvExport();
            // setupPerDeviceCsvExport();******Lưu ý quan trọng về việc xuất TOÀN BỘ dữ liệu cho từng thiết bị:******Hàm `exportTableDataToCsv` như trên sẽ chỉ xuất các dòng dữ liệu đang ___hiển thị___ trên trang cho bảng của thiết bị đó (do phân trang). Nếu bạn muốn xuất ___toàn bộ___ lịch sử dữ liệu của một thiết bị (không chỉ trang hiện tại), bạn cần:1) ******Truy cập dữ liệu đầy đủ:****** Biến `deviceDataMap` (được đề cập trong `initializeApp` của `data.html` và kế hoạch tối ưu hóa) lưu trữ toàn bộ telemetry data cho mỗi thiết bị. Bạn cần sử dụng `deviceDataMap.get(deviceId)` để lấy mảng dữ liệu đầy đủ.

2) ******Xây dựng CSV từ mảng dữ liệu:****** Thay vì duyệt qua các `<tr>`, `<td>` của DOM, bạn sẽ duyệt qua mảng dữ liệu này, định dạng từng mục thành một hàng CSV.******Ví dụ nâng cao cho** `setupPerDeviceCsvExport` **để xuất toàn bộ dữ liệu từ** `deviceDataMap`**:******            // (Đặt hàm này trong phần <script> của data.html)

            function exportAllDeviceDataFromMap(deviceId, filename) {
                // Giả sử deviceDataMap được khởi tạo và cập nhật trong scope có thể truy cập
                if (typeof deviceDataMap === 'undefined' || !deviceDataMap.has(deviceId)) {
                    alert(`Không tìm thấy dữ liệu đầy đủ cho thiết bị ID: ${deviceId}. Vui lòng thử lại sau khi dữ liệu được tải.`);
                    return;
                }

                const telemetryData = deviceDataMap.get(deviceId); // Đây là mảng các object telemetry
                if (!telemetryData || telemetryData.length === 0) {
                    alert('Không có dữ liệu telemetry để xuất cho thiết bị này.');
                    return;
                }

                const rows = [];
                // Xác định headers - bạn có thể muốn tùy chỉnh các cột này
                // Ví dụ: lấy keys từ object payload đầu tiên, hoặc định nghĩa cố định
                const headers = ['Timestamp', 'Topic Name', 'Payload Value', 'Payload Unit']; // Ví dụ headers
                // Hoặc tự động hơn:
                // const samplePayloadKeys = telemetryData.length > 0 && typeof telemetryData[0].payload === 'object' ? Object.keys(telemetryData[0].payload) : ['payload'];
                // const headers = ['Timestamp', 'Topic Name', ...samplePayloadKeys];
                rows.push(headers);

                telemetryData.forEach(item => {
                    const row = [];
                    row.push(moment(item.timestamp).format('YYYY-MM-DD HH:mm:ss'));
                    row.push(item.topic_name || item.topic_id); // Sử dụng topic_name nếu có

                    // Xử lý payload
                    if (typeof item.payload === 'object' && item.payload !== null) {
                        // Ví dụ đơn giản: lấy 'value' và 'unit' nếu có
                        row.push(item.payload.value !== undefined ? item.payload.value : JSON.stringify(item.payload));
                        row.push(item.payload.unit !== undefined ? item.payload.unit : '');
                        // Nếu muốn tất cả các key trong payload:
                        // samplePayloadKeys.forEach(key => {
                        //    row.push(item.payload[key] !== undefined ? item.payload[key] : '');
                        // });
                    } else {
                        row.push(item.payload); // Nếu payload là string hoặc number
                        // samplePayloadKeys.slice(1).forEach(() => row.push('')); // Điền rỗng cho các cột payload khác
                    }
                    rows.push(row);
                });

                let csvContent = "data:text/csv;charset=utf-8,";
                rows.forEach(function(rowArray) {
                    const row = rowArray.map(function(cell) {
                        let processedCell = (cell === null || cell === undefined) ? '' : cell.toString();
                        processedCell = processedCell.replace(/"/g, '""');
                        if (processedCell.includes(',') || processedCell.includes('"') || processedCell.includes('\n')) {
                            processedCell = '"' + processedCell + '"';
                        }
                        return processedCell;
                    }).join(",");
                    csvContent += row + "\r\n";
                });

                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download", filename);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }

            // Cập nhật hàm setupPerDeviceCsvExport để sử dụng hàm mới
            function setupPerDeviceCsvExport() {
                $('#device-cards').on('click', '.device-export', function() {
                    const deviceId = $(this).data('device-id');
                    const deviceName = $(this).closest('.device-card').find('.device-title h5').text().trim() || deviceId;
                    const filename = `device_${deviceName.replace(/\s+/g, '_')}_full_data.csv`;

                    // Gọi hàm xuất toàn bộ dữ liệu từ deviceDataMap
                    exportAllDeviceDataFromMap(deviceId, filename);
                });
            }
            
            // Đảm bảo deviceDataMap được khởi tạo và cập nhật trong initializeApp()
            // Trong initializeApp():
            // ...
            // // Initialize device data map for pagination and full export
            // Object.entries(currentDeviceData).forEach(([deviceId, info]) => {
            //    if (!deviceDataMap.has(deviceId) || JSON.stringify(deviceDataMap.get(deviceId)) !== JSON.stringify(info.telemetry)) {
            //        deviceDataMap.set(deviceId, info.telemetry);
            //    }
            // });
            // ...
            // Trong updateDeviceCardContent(deviceId, info):
            // ...
            // // Store/Update the device's full telemetry data for pagination and full export
            // if (!deviceDataMap.has(deviceId) || JSON.stringify(deviceDataMap.get(deviceId)) !== JSON.stringify(info.telemetry)) {
            //     deviceDataMap.set(deviceId, info.telemetry);
            // }
            // ...
------------------

### **3. Tổng kết và Khuyến nghị**

## - ****Kiểm tra kỹ lưỡng:**** Sau khi áp dụng các thay đổi này, hãy kiểm tra chức năng xuất CSV trên nhiều trình duyệt khác nhau.

- ****Xử lý ký tự đặc biệt:**** Logic escape ký tự trong CSV (`replace(/"/g, '""')` và bao quanh bằng `""`) là cơ bản. Nếu dữ liệu của bạn rất phức tạp, có thể cần một thư viện chuyên dụng hơn phía client hoặc thực hiện export ở backend.

- ****Xuất dữ liệu lớn:**** Đối với việc xuất một lượng rất lớn dữ liệu, thực hiện hoàn toàn ở phía client có thể gây treo trình duyệt. Trong trường hợp đó, nên cân nhắc việc tạo file CSV ở phía server và cho phép người dùng tải về. Điều này sẽ yêu cầu một API endpoint mới ở backend (ví dụ: `/api/export_device_data/<device_id>`).Với các thay đổi trên, chức năng xuất CSV của bạn sẽ hoạt động chính xác hơn và thân thiện với người dùng hơn.
