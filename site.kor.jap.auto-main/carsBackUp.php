<?php
// Подключение
$mysqli = new mysqli("localhost", "root", "", "mysite");

// Проверка подключения
if ($mysqli->connect_error) {
    die('Ошибка подключения (' . $mysqli->connect_errno . ') ' . $mysqli->connect_error);
}

// Запрос данных из базы данных (для таблицы cars)
$result_cars = $mysqli->query("SELECT * FROM cars");

// Запрос данных из базы данных (для таблицы kia-cars)
$result_kia_cars = $mysqli->query("SELECT * FROM `kia-cars`");

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="./styles/product.css"/>
    <title>Галерея</title>
</head>
<body>

<div class="BigCarName">parasha</div>

<!-- ... your existing code ... -->

<!-- Блок для данных из таблицы cars -->
<div>
    <h2>Cars</h2>
    <ul class="catCardList">
        <?php
        if ($result_cars && $result_cars->num_rows > 0) {
            while ($row = $result_cars->fetch_assoc()) {
                ?>
                <li class="catCardList">
                    <div class="catCard">
                        <!-- Modify the link to include the product ID -->
                        <a href="product.php?id=<?php echo $row['id']; ?>">
                            <img src="img/<?php echo $row['картинка']; ?>" alt="<?php echo $row['название']; ?>">
                        </a>
                        <!-- ... rest of your code ... -->
                    </div>
                </li>
                <?php
            }
        } else {
            echo 'Нет доступных продуктов.';
        }
        ?>
    </ul>
</div>

<!-- Блок для данных из таблицы kia-cars -->
<div>
    <h2>Kia Cars</h2>
    <ul class="catCardList">
        <?php
        // Проверка наличия данных в результате запроса
        if ($result_kia_cars && $result_kia_cars->num_rows > 0) {
            // Обработка каждой строки результата
            while ($row = $result_kia_cars->fetch_assoc()) {
                ?>
                <li class="catCardList">
                    <div class="catCard">
                        <a href="product.php?name=<?php echo urlencode($row['название']); ?>">
                            <img src="img/<?php echo $row['картинка']; ?>" alt="<?php echo $row['название']; ?>">
                        </a>
                        <div class="lowerCatCard">
                            <h3><?php echo $row['название']; ?></h3>
                            <div class="startingPrice">Prices Starting At <span>$<?php echo $row['цена']; ?></span></div>
                            <p><?php echo $row['описание']; ?></p>
                            <!-- Добавьте другие поля, если необходимо -->
                            <div id="catCardButton" class="button">
                                <a href="product.php?name=<?php echo urlencode($row['название']); ?>">View Product</a>
                            </div>
                        </div>
                    </div>
                </li>
                <?php
            }
        } else {
            // Вывод сообщения, если нет данных
            echo 'Нет доступных продуктов.';
        }
        ?>
    </ul>
</div>

<!-- Закрытие соединения с базой данных -->
<?php
$mysqli->close();
?>
</body>
</html>
