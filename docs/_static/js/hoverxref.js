var mathjax = true;
var sphinxtabs = true;



function reRenderTooltip (instance, helper) {
    // Check if the content is the same as the default content until
    // it's different. Once it's different, re renders its content
    // to show it properly (this may involve calling external JS
    // libraries like MathJax) and finally call tooltip.reposition().
    if (helper.tooltip.textContent !== 'Loading...') {
        // https://stackoverflow.com/questions/5200545/how-to-recall-or-restart-mathjax
        if (mathjax) {
            if (typeof MathJax !== 'undefined') {
                reLoadMathJax(helper.tooltip.id);
            } else {
                console.debug('Not triggering MathJax because it is not defined');
            };

        };
        instance.reposition();
    } else {
        setTimeout(reRenderTooltip, 100, instance, helper);
    };
}


function reLoadMathJax(elementId) {
    console.debug('Triggering MathJax.Hub.Typeset()');
    MathJax.Hub.Queue((["Typeset", MathJax.Hub, elementId]));
}


function reLoadSphinxTabs() {
    if (sphinxtabs) {
        // https://github.com/djungelorm/sphinx-tabs
        console.debug('Triggering Sphinx Tabs rendering');
        (function(d, script) {
            // HACK: please, improve this code to call the content of "tab.js" without creating a script element

            // Get the URL from the current generated page since it's not always the same
            var src = $('script[src$="sphinx_tabs/tabs.js"]')[0].src;

            script = d.createElement('script');
            script.type = 'text/javascript';
            script.onload = function(){
                // remote script has loaded
            };
            script.src = src;
            d.getElementsByTagName('head')[0].appendChild(script);

            // Once the script has been executed, we remove it from the DOM
            script.parentNode.removeChild(script);
        }(document));
    };
};

function getEmbedURL(project, version, doc, docpath, section) {
    var params = {
        'project': project,
        'version': version,
        'doc': doc,
        'path': docpath,
        'section': section,
    }
    console.debug('Data: ' + JSON.stringify(params));
    var url = 'http://localhost:8000' + '/api/v2/embed/?' + $.param(params);
    console.debug('URL: ' + url);
    return url
}


$(document).ready(function() {
    $('.hoverxref.tooltip').tooltipster({
        theme: ['tooltipster-shadow', 'tooltipster-shadow-custom'],
        interactive: true,
        maxWidth: 650,
        animation: 'fade',
        animationDuration: 0,
        side: 'right',
        content: 'Loading...',

        functionBefore: function(instance, helper) {
            var $origin = $(helper.origin);
            var project = $origin.data('project');
            var version = $origin.data('version');
            var doc = $origin.data('doc');
            var docpath = $origin.data('docpath');
            var section = $origin.data('section');


            // we set a variable so the data is only loaded once via Ajax, not every time the tooltip opens
            if ($origin.data('loaded') !== true) {
                var url = getEmbedURL(project, version, doc, docpath, section);
                $.get(url, function(data) {
                    // call the 'content' method to update the content of our tooltip with the returned data.
                    // note: this content update will trigger an update animation (see the updateAnimation option)
                    instance.content(data['content']);

                    // to remember that the data has been loaded
                    $origin.data('loaded', true);
                });
            }
        },

        functionReady: function(instance, helper) {
            // most of Read the Docs Sphinx theme bases its style on "rst-content".
            // We add that class to the tooltipser HTML tag here by default or a user-defined one.
            helper.tooltip.classList.add('rst-content');
            reLoadSphinxTabs();
            setTimeout(
                reRenderTooltip,
                50,
                instance,
                helper
            );
        }
    })

    var modalHtml = `
  <div class="modal micromodal-slide md-typeset" id="micromodal" aria-hidden="true">
    <div class="modal__overlay" tabindex="-1" data-micromodal-close>
      <div class="modal__container" role="dialog" aria-modal="true" aria-labelledby="micromodal-title">
        <header class="modal__header">
          <h1 class="modal__title" id="micromodal-title"></h1>
          <button class="modal__close" aria-label="Close modal" data-micromodal-close></button>
        </header>
        <hr/>
        <main class="modal__content" id="micromodal-content"></main>
        <footer class="modal__footer">
          <button class="modal__btn" data-micromodal-close aria-label="Close this dialog window">Close</button>
        </footer>
      </div>
    </div>
  </div>
`
    $('body').append(modalHtml);

    
    function onShow(modal, element) {
        // This is a HACK to get some "smart" left position of the
        // modal depending its size.
        var container = $('#micromodal .modal__container')
        var maxWidth = $('.wy-nav-content').innerWidth() - 150;
        var contentLeft = $('.wy-nav-content').position().left;
        if (container.width() >= maxWidth) {
            var left = contentLeft - 150;
        }
        else {
            var left = contentLeft + 150;
        }
        console.debug('Container left position: ' + left);
        container.css('left', left);
    }
    

    function showModal(element) {
        var project = element.data('project');
        var version = element.data('version');
        var doc = element.data('doc');
        var docpath = element.data('docpath');
        var section = element.data('section');

        var url = getEmbedURL(project, version, doc, docpath, section);
        $.get(url, function(data) {
            var content = $('<div></div>');
            content.html(data['content'][0]);

            var h1 = $('h1:first', content);
            var title = h1.text()
            if (title) {
                var link = $('a', h1).attr('href') || '#';
                var a = $('<a></a>').attr('href', link).text('📝 ' + title.replace('¶', ''));
            }
            else {
                var a = '📝 Note';
            }
            h1.replaceWith('');

            $('#micromodal-title').html(a);
            $('#micromodal-content').html(content);
            MicroModal.show('micromodal', {
                
                onShow: onShow,
                
                openClass: 'is-open',
                disableScroll: false,
                disableFocus: true,
                awaitOpenAnimation: false,
                awaitCloseAnimation: false,
                debugMode: false
            });
            $('#micromodal .modal__container').scrollTop(0);
            reLoadSphinxTabs();
            if (mathjax) {
                if (typeof MathJax !== 'undefined') {
                    reLoadMathJax('micromodal');
                } else {
                    console.debug('Not triggering MathJax because it is not defined');
                };
            };
        });
    };

    var delay = 350, setTimeoutConst;
    $('.hoverxref.modal').hover(function(event) {
        var element = $(this);
        console.debug('Event: ' + event + ' Element: ' + element);
        event.preventDefault();

        setTimeoutConst = setTimeout(function(){
            showModal(element);
        }, delay);
    }, function(){
        clearTimeout(setTimeoutConst);
    });
});