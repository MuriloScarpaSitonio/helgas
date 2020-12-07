let thumbnails = document.getElementsByClassName('thumbnails')

let activeImages = document.getElementsByClassName('active')

for (var i = 0; i < thumbnails.length; i++) {

	thumbnails[i].addEventListener('click', function () {
		activeImages[1].classList.remove('active')
		this.classList.add('active')
		document.getElementById('featured').src = this.src
	})
}
