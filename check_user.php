<?php
// Database connection
$host = 'localhost';
$db   = 'users_db';
$user = 'root';
$pass = 'root';
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$opt = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];
$pdo = new PDO($dsn, $user, $pass, $opt);

// Get the username, email and phone from the POST request
$username = $_POST['username'];
$email = $_POST['email'];
$phone = $_POST['phone'];

// Prepare a SELECT statement to check if the user exists
$stmt = $pdo->prepare('SELECT * FROM users WHERE username = ? AND email = ? AND phone_number = ?');
$stmt->execute([$username, $email, $phone]);
$user = $stmt->fetch();

if ($user) {
    // If the user exists, return 'login'
    echo 'login';
} else {
    // Prepare SELECT statements to check if the username, email or phone number already exists
    $stmtUsername = $pdo->prepare('SELECT * FROM users WHERE username = ?');
    $stmtEmail = $pdo->prepare('SELECT * FROM users WHERE email = ?');
    $stmtPhone = $pdo->prepare('SELECT * FROM users WHERE phone_number = ?');

    $stmtUsername->execute([$username]);
    $stmtEmail->execute([$email]);
    $stmtPhone->execute([$phone]);

    $userUsername = $stmtUsername->fetch();
    $userEmail = $stmtEmail->fetch();
    $userPhone = $stmtPhone->fetch();

    if ($userUsername || $userEmail || $userPhone) {
        // If the username, email or phone number exists, return 'exists'
        echo 'exists';
    } else {
        // If the user does not exist, insert a new row into the table
        $stmt = $pdo->prepare('INSERT INTO users (username, email, phone_number) VALUES (?, ?, ?)');
        $stmt->execute([$username, $email, $phone]);
        echo 'created';
    }
}
?>
