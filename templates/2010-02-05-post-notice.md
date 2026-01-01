---
title: "Post: Notice"
categories:
  - Blog
tags:
  - Post Formats
  - notice
---

A notice displays information that explains nearby content. Often used to call attention to a particular detail.

When using Kramdown `{: .notice}` can be added after a sentence to assign the `.notice` to the `<p></p>` element. 

**Changes in Service:** We just updated our [privacy policy](#) here to better service our customers. We recommend reviewing the changes.
{: .notice}

**Primary Notice:** Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. [Praesent libero](#). Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
{: .notice--primary}

**Info Notice:** Lorem ipsum dolor sit amet, [consectetur adipiscing elit](#). Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
{: .notice--info}

**Warning Notice:** Lorem ipsum dolor sit amet, consectetur adipiscing elit. [Integer nec odio](#). Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
{: .notice--warning}

**Danger Notice:** Lorem ipsum dolor sit amet, [consectetur adipiscing](#) elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
{: .notice--danger}

**Success Notice:** Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at [nibh elementum](#) imperdiet.
{: .notice--success}

Want to wrap several paragraphs or other elements in a notice? Using Liquid to capture the content and then filter it with `markdownify` is a good way to go.

```html
{% raw %}{% capture notice-2 %}
#### New Site Features

* You can now have cover images on blog pages
* Drafts will now auto-save while writing
{% endcapture %}{% endraw %}

<div class="notice">{% raw %}{{ notice-2 | markdownify }}{% endraw %}</div>
```

{% capture notice-2 %}
#### New Site Features

* You can now have cover images on blog pages
* Drafts will now auto-save while writing
{% endcapture %}

<div class="notice">
  {{ notice-2 | markdownify }}
</div>

Or you could skip the capture and stick with straight HTML.

```html
<div class="notice">
  <h4>Message</h4>
  <p>A basic message.</p>
</div>
```

<div class="notice">
  <h4>Message</h4>
  <p>A basic message.</p>
</div>


## Leave a Comment

Note, I use [Remarkbox](https://www.remarkbox.com/) for comments to prevent Disqus from showing adds or other methods requiring a GitHub login for participation in any discussions. Although you are asked for you email, there is no need to verify it through remarkbox in order to leave a comment. Verification is just so you can track discussions, etc. without the system treating you as a new person every time.  

<!-- Remarkbox - Your readers want to communicate with you -->
<div id="remarkbox-div">
  <noscript>
    <iframe id=remarkbox-iframe src="https://my.remarkbox.com/embed?nojs=true&mode=light" style="height:600px;width:100%;border:none!important" tabindex=0></iframe>
  </noscript>
</div>
<script src="https://my.remarkbox.com/static/js/iframe-resizer/iframeResizer.min.js"></script>
<script>
  var rb_owner_key = "a11e8d2f-cd40-11f0-ad89-040140774501";
  var thread_uri = window.location.href;
  var thread_title = window.document.title;
  var thread_fragment = window.location.hash;

  // rb owner was here.
  var rb_src = "https://my.remarkbox.com/embed" +
      "?rb_owner_key=" + rb_owner_key +
      "&thread_title=" + encodeURI(thread_title) +
      "&thread_uri=" + encodeURIComponent(thread_uri) +
      "&mode=light" +
      thread_fragment;

  function create_remarkbox_iframe() {
    var ifrm = document.createElement("iframe");
    ifrm.setAttribute("id", "remarkbox-iframe");
    ifrm.setAttribute("scrolling", "no");
    ifrm.setAttribute("src", rb_src);
    ifrm.setAttribute("frameborder", "0");
    ifrm.setAttribute("tabindex", "0");
    ifrm.setAttribute("title", "Remarkbox");
    ifrm.style.width = "100%";
    document.getElementById("remarkbox-div").appendChild(ifrm);
  }
  create_remarkbox_iframe();
  iFrameResize(
    {
      checkOrigin: ["https://my.remarkbox.com"],
      inPageLinks: true,
      initCallback: function(e) {e.iFrameResizer.moveToAnchor(thread_fragment)}
    },
    document.getElementById("remarkbox-iframe")
  );
</script>