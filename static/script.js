$(document).ready(function() {
  // Captura el evento submit del formulario
  $('#recomendacion-form').submit(function(event) {
    // Evita que se envíe el formulario de forma convencional
    event.preventDefault();
    // Obtiene los valores del formulario
    var longitud = $('input[name="longitud"]:checked').val();
    var genero = $('input[name="genero"]:checked').val();
    // Envía los valores al servidor mediante una petición POST
    $.ajax({
      type: 'POST',
      url: '/',
      data: {'longitud': longitud, 'genero': genero},
      success: function(response) {
        // Actualiza el contenido del elemento con id 'recomendacion' con la respuesta del servidor
        $('#recomendacion').html(response);
        // Cambia la posición del botón según la altura de sinopsis2
        var sinopsis2Height = $('.recomendacion-sinopsis2').height();
        var enviarButtonTop = $('.recomendacion-sinopsis2').offset().top + sinopsis2Height + 10;
        $('.recomendacion-enviar').css('top', enviarButtonTop);
      }
    });
    });
});



