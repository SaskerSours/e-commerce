  function changeColor() {
    document.getElementById("myButton").style.backgroundColor = "black";
  }

const priceRange = document.getElementById("price-range");
const selectedPrice = document.getElementById("selected-price");
const products = document.querySelectorAll(".product");

priceRange.addEventListener("input", updateSelectedPrice);

function updateSelectedPrice() {
    // Получаем значение ползунка
    const selectedValue = parseInt(priceRange.value);

    // Обновляем текст с выбранной ценой
    selectedPrice.textContent = selectedValue;

    // Перебираем все продукты и скрываем те, цена которых не соответствует выбранной
    products.forEach(product => {
        const productPrice = parseInt(product.getAttribute("data-price"));
        if (productPrice <= selectedValue) {
            product.style.display = "block";
        } else {
            product.style.display = "none";
        }
    });
}