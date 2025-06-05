<?php
header('Content-Type: text/html; charset=utf-8');

// Extract instrument ID from POST data
$SN = isset($_POST["SN"]) ? trim($_POST["SN"]) : '';

if (empty($SN)) {
    die("Error: No serial number provided");
}

// Create sample data file if it doesn't exist
$sampleData = <<<EOD
Serial_Number A B C beta tau
WV2-157 0.123 0.456 0.789 0.234 0.567
WV2-158 0.234 0.567 0.890 0.345 0.678
WV2-159 0.345 0.678 0.901 0.456 0.789
EOD;

$dataFile = "wvdata.dat";
if (!file_exists($dataFile)) {
    file_put_contents($dataFile, $sampleData);
}

// Open WV instrument calibration constant file safely
if (!file_exists($dataFile) || !is_readable($dataFile)) {
    die("Error: Calibration data file is missing or unreadable.");
}

$in = fopen($dataFile, "r");
if (!$in) {
    die("Error: Can't open calibration data file");
}

// Read header line
$header = fgets($in);

$found = false;
while (($line = fgets($in)) !== false) {
    $values = sscanf(trim($line), "%s %f %f %f %f %f");
    if ($values && count($values) == 6) {
        list($SN_dat, $A, $B, $C, $beta, $tau) = $values;
        if (strcasecmp($SN_dat, $SN) == 0) {
            $found = true;
            break;
        }
    }
}

fclose($in);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calibration Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }

        th {
            background-color: #f8f9fa;
        }

        .header-row {
            background-color: #eee;
            font-weight: bold;
        }

        .back-button {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }

        .back-button:hover {
            background-color: #2980b9;
        }

        .error {
            color: #e74c3c;
            padding: 20px;
            background-color: #fadbd8;
            border-radius: 4px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <?php if ($found): ?>
            <table>
                <tr>
                    <th>Quantity</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Instrument ID</td>
                    <td><?php echo htmlspecialchars($SN); ?></td>
                </tr>
                <tr class="header-row">
                    <td colspan="2">Calibration Constants</td>
                </tr>
                <tr>
                    <td>A</td>
                    <td><?php echo number_format($A, 6); ?></td>
                </tr>
                <tr>
                    <td>B</td>
                    <td><?php echo number_format($B, 6); ?></td>
                </tr>
                <tr>
                    <td>C</td>
                    <td><?php echo number_format($C, 6); ?></td>
                </tr>
                <tr>
                    <td>tau</td>
                    <td><?php echo number_format($tau, 6); ?></td>
                </tr>
                <tr>
                    <td>beta</td>
                    <td><?php echo number_format($beta, 6); ?></td>
                </tr>
            </table>
        <?php else: ?>
            <div class="error">
                Couldn't find instrument with Serial Number: <?php echo htmlspecialchars($SN); ?>
            </div>
        <?php endif; ?>
        
        <a href="index.html" class="back-button">Back to Search</a>
    </div>
</body>
</html>
