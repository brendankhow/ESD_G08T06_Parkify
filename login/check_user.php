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

// Get the username and email from the POST request
$username = $_POST['username'];
$email = $_POST['email'];

// Prepare a SELECT statement to check if the user exists
$stmt = $pdo->prepare('SELECT * FROM users WHERE username = ? AND email = ?');
$stmt->execute([$username, $email]);
$user = $stmt->fetch();

if ($user) {
    // If the user exists, return 'exists'
    echo 'exists';
} else {
    // If the user does not exist, insert a new row into the table
    $stmt = $pdo->prepare('INSERT INTO users (username, email) VALUES (?, ?)');
    $stmt->execute([$username, $email]);
    echo 'created';
}
?>
