<?php
$mysqli = new mysqli("localhost", "root", "", "mysite");

if ($mysqli->connect_error) {
    die('Ошибка подключения (' . $mysqli->connect_errno . ') ' . $mysqli->connect_error);
}

// Получение ID продукта из URL
$productId = $_GET['id'];

// Проверка наличия значения $productId
if ($productId === null) {
    echo 'ID продукта не указан.';
    exit;
}

// Запрос данных продукта по ID
$query = $mysqli->prepare("SELECT * FROM cars WHERE id = ?");
$query->bind_param("i", $productId);
$query->execute();
$result = $query->get_result();

if ($result && $result->num_rows > 0) {
    $row = $result->fetch_assoc();
    ?>
    <!DOCTYPE html>
    <html lang="en">
    <!-- ... your existing code ... -->
    <body>
    <div class="qwezxc"><?php echo $row['название']; ?></div>
    <img src="img/<?php echo $row['картинка']; ?>" alt="<?php echo $row['название']; ?>">






    <div class="lowerCatCard">
        <div class="qweqweqweq"><?php echo $row ['описание']               ;?></div>

        <div class="qweqweqweq"><?php echo $row ['цена']               ;?></div>

        <img src="img/<?php echo $row['большая_картинка']; ?>" alt="<?php echo $row['название']; ?>">


    </div>
    </body>
    </html>
    <?php
} else {
    echo 'Продукт не найден';
}

$query->close();
$mysqli->close();
?>
