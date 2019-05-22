$(document).ready(function() {
    $(".enter-link").on("click", function(event) {
        if (!$(event.target).is('a')) {
            $(this).find("a")[0].click();
        }
    });
    $(".menu-hide-control")[0].style.width = '40px';
    $(".content")[0].style.marginLeft = '40px';
    $(".menu-hideable").hide();
    $(".sub-menu-hideable").hide();
    $(".image-hideable").hide();
    $(".image-min-hideable").show();
    $(".menu-hide-control").hover(function() {
        var fadeDuration = 500;
        var delayDuration = 300;
        $(".menu-hide-control").stop( true, true ).animate({ width: '300px' });
        //$(".content").stop( true, true ).animate({ marginLeft: '300px' });
        $(".menu-hideable").delay(delayDuration).fadeIn(fadeDuration);
        $(".sub-menu-hideable").delay(delayDuration).fadeIn(fadeDuration);
        $(".image-hideable").delay(delayDuration).fadeIn(fadeDuration);
        resize_graphs();
    }, function() {
        $(".menu-hideable").stop( true, true ).hide();
        $(".sub-menu-hideable").stop( true, true ).hide();
        $(".image-hideable").stop( true, true ).hide();
        $(".menu-hide-control").animate({width: '40px'});
        //$(".content").animate({marginLeft: '40px'});
    });
});