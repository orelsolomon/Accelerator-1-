<?php

$server_name = "localhost";
$user_name = "isorelsu_user123";
$password = "Rotem123456789!";
$database_name = "isorelsu_SmartSip";

// Create connection
$conn = new mysqli($server_name, $user_name, $password, $database_name);

// Check the connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Get info from HTML form
$full_name = $_POST['full_name'];
$family_fk = $_POST['family_fk'];
$city = $_POST['city'];

// Prepare the SQL statement
$stmt = $conn->prepare("INSERT INTO customerPlants (full_name, family_fk, city) VALUES (?, ?, ?)");

// Bind parameters
// Assuming family_fk is a string. If it's an integer, change "sss" to "sis".
$stmt->bind_param("sss", $full_name, $family_fk, $city);

// Execute the statement
if ($stmt->execute()) {
    $message = "Your plant added successfully!";
} else {
    $message = "Cannot add a new plant. Error is: " . $stmt->error;
}

// Close the statement
$stmt->close();

// Close the connection
$conn->close();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Response</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Response</h1>
        <div id="response" class="form-group"><?php echo $message; ?></div>
        
        <!-- Button to move to index.html -->
        <?php if ($message === "Your plant added successfully!"): ?>
            <button class="btn" onclick="moveToIndex()">Go to Index</button>
        <?php endif; ?>
    </div>
    
    <script>
        // Function to move to index.html
        function moveToIndex() {
            window.location.href = "index.html";
        }
    </script>
</body>
</html>
