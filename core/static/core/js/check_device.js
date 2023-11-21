function check_mobile() {
   const isMobile = {
      Android: function () {
         return navigator.userAgent.match(/Android/i);
      },
      BlackBerry: function () {
         return navigator.userAgent.match(/BlackBerry/i);
      },
      IOS: function () {
         return navigator.userAgent.match(/iPhone|iPad|iPod/i);
      },
      Opera: function () {
         return navigator.userAgent.match(/Opera Mini/i);
      },
      Windows: function () {
         return navigator.userAgent.match(/IEMobile/i);
      },
      any: function () {
         return (
            isMobile.Android() ||
            isMobile.BlackBerry() ||
            isMobile.IOS() ||
            isMobile.Opera() ||
            isMobile.Windows()
         );
      }
   };

   if (isMobile.any()) {
      document.body.classList.add('_touch');
      if(document.getElementsByClassName('menu__burger-btn').length!==0){
         document.getElementsByClassName('menu__burger-btn')[0].addEventListener('click', function (e) {
            if (reg_active === true) {
               document.getElementsByClassName('wrapper')[0].classList.remove('_active_reg-form');
               reg_active = false
            }
            else {
               document.getElementsByTagName('header')[0].classList.toggle('_when-menu-on');
               document.getElementsByClassName('header__menu')[0].classList.toggle('_active_menu');
               document.getElementsByClassName('wrapper')[0].classList.remove('_active_reg-form');
            }
            document.getElementsByClassName('body')[0].classList.toggle('_active_menu_OnBody');
         });
      }
   }
   else {
      document.body.classList.add('_pc');
      if(document.getElementsByClassName('menu__burger-btn').length !== 0){
         document.getElementsByClassName('menu__burger-btn')[0].style.display = 'none';
      }
   }
}
check_mobile();