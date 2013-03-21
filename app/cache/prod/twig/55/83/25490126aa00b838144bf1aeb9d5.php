<?php

/* TwigBundle:Exception:traces.html.twig */
class __TwigTemplate_558325490126aa00b838144bf1aeb9d5 extends Twig_Template
{
    public function __construct(Twig_Environment $env)
    {
        parent::__construct($env);

        $this->parent = false;

        $this->blocks = array(
        );
    }

    protected function doDisplay(array $context, array $blocks = array())
    {
        // line 1
        echo "<div class=\"block\">
    ";
        // line 2
        if (isset($context["count"])) { $_count_ = $context["count"]; } else { $_count_ = null; }
        if (($_count_ > 0)) {
            // line 3
            echo "        <h2>
            <span><small>[";
            // line 4
            if (isset($context["count"])) { $_count_ = $context["count"]; } else { $_count_ = null; }
            if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
            echo twig_escape_filter($this->env, (($_count_ - $_position_) + 1), "html", null, true);
            echo "/";
            if (isset($context["count"])) { $_count_ = $context["count"]; } else { $_count_ = null; }
            echo twig_escape_filter($this->env, ($_count_ + 1), "html", null, true);
            echo "]</small></span>
            ";
            // line 5
            if (isset($context["exception"])) { $_exception_ = $context["exception"]; } else { $_exception_ = null; }
            echo $this->env->getExtension('code')->abbrClass($this->getAttribute($_exception_, "class"));
            echo ": ";
            if (isset($context["exception"])) { $_exception_ = $context["exception"]; } else { $_exception_ = null; }
            echo $this->env->getExtension('code')->formatFileFromText(nl2br(twig_escape_filter($this->env, $this->getAttribute($_exception_, "message"), "html", null, true)));
            echo "&nbsp;
            ";
            // line 6
            ob_start();
            // line 7
            echo "            <a href=\"#\" onclick=\"toggle('traces-";
            if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
            echo twig_escape_filter($this->env, $_position_, "html", null, true);
            echo "', 'traces'); switchIcons('icon-traces-";
            if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
            echo twig_escape_filter($this->env, $_position_, "html", null, true);
            echo "-open', 'icon-traces-";
            if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
            echo twig_escape_filter($this->env, $_position_, "html", null, true);
            echo "-close'); return false;\">
                <img class=\"toggle\" id=\"icon-traces-";
            // line 8
            if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
            echo twig_escape_filter($this->env, $_position_, "html", null, true);
            echo "-close\" alt=\"-\" src=\"data:image/gif;base64,R0lGODlhEgASAMQSANft94TG57Hb8GS44ez1+mC24IvK6ePx+Wa44dXs92+942e54o3L6W2844/M6dnu+P/+/l614P///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAABIALAAAAAASABIAQAVCoCQBTBOd6Kk4gJhGBCTPxysJb44K0qD/ER/wlxjmisZkMqBEBW5NHrMZmVKvv9hMVsO+hE0EoNAstEYGxG9heIhCADs=\" style=\"visibility: ";
            if (isset($context["count"])) { $_count_ = $context["count"]; } else { $_count_ = null; }
            echo (((0 == $_count_)) ? ("visible") : ("hidden"));
            echo "\" />
                <img class=\"toggle\" id=\"icon-traces-";
            // line 9
            if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
            echo twig_escape_filter($this->env, $_position_, "html", null, true);
            echo "-open\" alt=\"+\" src=\"data:image/gif;base64,R0lGODlhEgASAMQTANft99/v+Ga44bHb8ITG52S44dXs9+z1+uPx+YvK6WC24G+944/M6W28443L6dnu+Ge54v/+/l614P///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAABMALAAAAAASABIAQAVS4DQBTiOd6LkwgJgeUSzHSDoNaZ4PU6FLgYBA5/vFID/DbylRGiNIZu74I0h1hNsVxbNuUV4d9SsZM2EzWe1qThVzwWFOAFCQFa1RQq6DJB4iIQA7\" style=\"visibility: ";
            if (isset($context["count"])) { $_count_ = $context["count"]; } else { $_count_ = null; }
            echo (((0 == $_count_)) ? ("hidden") : ("visible"));
            echo "; margin-left: -18px\" />
            </a>
            ";
            echo trim(preg_replace('/>\s+</', '><', ob_get_clean()));
            // line 12
            echo "        </h2>
    ";
        } else {
            // line 14
            echo "        <h2>Stack Trace</h2>
    ";
        }
        // line 16
        echo "
    <a id=\"traces-link-";
        // line 17
        if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
        echo twig_escape_filter($this->env, $_position_, "html", null, true);
        echo "\"></a>
    <ol class=\"traces list-exception\" id=\"traces-";
        // line 18
        if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
        echo twig_escape_filter($this->env, $_position_, "html", null, true);
        echo "\" style=\"display: ";
        if (isset($context["count"])) { $_count_ = $context["count"]; } else { $_count_ = null; }
        echo (((0 == $_count_)) ? ("block") : ("none"));
        echo "\">
        ";
        // line 19
        if (isset($context["exception"])) { $_exception_ = $context["exception"]; } else { $_exception_ = null; }
        $context['_parent'] = (array) $context;
        $context['_seq'] = twig_ensure_traversable($this->getAttribute($_exception_, "trace"));
        foreach ($context['_seq'] as $context["i"] => $context["trace"]) {
            // line 20
            echo "            <li>
                ";
            // line 21
            if (isset($context["position"])) { $_position_ = $context["position"]; } else { $_position_ = null; }
            if (isset($context["i"])) { $_i_ = $context["i"]; } else { $_i_ = null; }
            if (isset($context["trace"])) { $_trace_ = $context["trace"]; } else { $_trace_ = null; }
            $this->env->loadTemplate("TwigBundle:Exception:trace.html.twig")->display(array("prefix" => $_position_, "i" => $_i_, "trace" => $_trace_));
            // line 22
            echo "            </li>
        ";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['i'], $context['trace'], $context['_parent'], $context['loop']);
        $context = array_merge($_parent, array_intersect_key($context, $_parent));
        // line 24
        echo "    </ol>
</div>
";
    }

    public function getTemplateName()
    {
        return "TwigBundle:Exception:traces.html.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  114 => 22,  109 => 21,  106 => 20,  101 => 19,  85 => 16,  77 => 12,  67 => 9,  28 => 4,  47 => 7,  38 => 5,  24 => 4,  50 => 7,  110 => 20,  89 => 16,  65 => 14,  63 => 13,  58 => 12,  34 => 5,  26 => 4,  221 => 90,  207 => 82,  197 => 74,  195 => 73,  192 => 72,  189 => 71,  186 => 70,  181 => 67,  178 => 66,  173 => 63,  162 => 59,  158 => 57,  155 => 56,  152 => 55,  142 => 47,  136 => 44,  133 => 43,  130 => 42,  120 => 40,  105 => 31,  100 => 19,  75 => 24,  53 => 19,  60 => 21,  57 => 9,  43 => 8,  25 => 3,  39 => 7,  19 => 1,  98 => 40,  88 => 17,  80 => 15,  78 => 25,  46 => 9,  44 => 9,  40 => 7,  36 => 6,  32 => 12,  27 => 3,  22 => 2,  232 => 82,  226 => 78,  222 => 76,  215 => 73,  211 => 84,  208 => 70,  202 => 68,  196 => 64,  193 => 63,  187 => 62,  183 => 60,  180 => 59,  171 => 54,  166 => 51,  163 => 50,  160 => 49,  157 => 48,  149 => 42,  146 => 41,  140 => 46,  137 => 37,  129 => 36,  124 => 35,  121 => 24,  118 => 33,  115 => 39,  111 => 30,  107 => 28,  104 => 27,  97 => 24,  93 => 18,  90 => 21,  81 => 14,  70 => 23,  66 => 13,  62 => 12,  59 => 8,  56 => 20,  52 => 11,  49 => 10,  45 => 6,  41 => 8,  37 => 5,  33 => 4,  30 => 4,);
    }
}
