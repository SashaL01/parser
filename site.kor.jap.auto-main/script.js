document.addEventListener("DOMContentLoaded", function () {
    var loremSections = document.querySelectorAll(".loremSection");
  
    function isInViewport(element) {
      var rect = element.getBoundingClientRect();
      var windowHeight = window.innerHeight || document.documentElement.clientHeight;
  
      return rect.top <= windowHeight * (2 / 3);
    }
  
    function revealContent(section) {
      var loremTextContainer = section.querySelector(".loremTextContainer");
      var loremImageContainer = section.querySelector(".loremImageContainer");
  
      loremTextContainer.classList.add("show");
      loremImageContainer.classList.add("show");
    }
  
    function handleScroll() {
      loremSections.forEach(function (section) {
        if (isInViewport(section) && !section.classList.contains("show")) {
          section.classList.add("show");
          revealContent(section);
        }
      });
    }
  
    window.addEventListener("scroll", handleScroll);
    handleScroll(); // Check if the sections are in view on page load
  });
  