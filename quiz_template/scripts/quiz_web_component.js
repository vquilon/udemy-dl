const WRONG_QUIZ = "wrong_quiz";
const QUIZ = "quiz";
const RESULTS = "results";
const REVISION = "revision";

const ANSWER_TEMPLATE = `<label><input type="radio" name="answer" value="{ANS_OPT}" group="answers">{ANS_TEXT}</label>`;
const ANSWERED_MSG = {
  "correct": "You answered {} questions correctly",
  "wrong": "You answered {} questions wrong",
  "skipped": "You skipped {} questions"
}

const SECTION_TEMPLATE=`<p class="sect-name"></p>`;
const SECTION_PROGRESS_TEMPLATE = `<div class="progress sect-correct"><label class="percent"></label></div><div class="progress sect-wrong"><label class="percent"></label></div><div class="progress sect-skipped"><label class="percent"></label></div>`;
const FEEDBACK_STYLES = {
  "correct": {
    "backgroundColor": "#46a049",
    "color": "fff"
  },
  "wrong": {
    "backgroundColor": "#f35b5b",
    "color": "fff"
  },
  "skipped": {
    "backgroundColor": "#aeaeae",
    "color": "fff"
  }
}

const template_styles = document.createElement("template");
template_styles.innerHTML = `
<link href="styles/quiz_styles.css" rel="stylesheet" type="text/css">
`

const template_wrong_quiz = document.createElement("template");
template_wrong_quiz.innerHTML = `
<div class="${WRONG_QUIZ} main hide">
  <div class="meta">
      <h1 class="name"></h1>
  </div>
  <div class="main-container">
    <p class="wrong-reason"></p>
  </div>
</div>
`;

const template_quiz = document.createElement("template");
template_quiz.innerHTML = `
<div class="${QUIZ} main hide">
  <div class="meta">
    <h1 class="name"></h1>
  </div>
  <div class="main-container">
    <p class="question"></p>
    <div class="feedbacks"></div>
    <div class="options answers"></div>
  </div>
  <button class="verify submit">Verify</button>
  <button class="skip submit">Skip</button>
  <input class="next_que" hidden>
</div>
`;

const template_results = document.createElement("template");
template_results.innerHTML = `
<div class="${RESULTS} main hide">
  <div class="meta">
    <h1 class="name"></h1>
    <p class="scoreboard"></p>
    <div class="overall-sections"></div>
  </div>
  <div class="main-container">
    <div class="skipped"></div>
    <div class="wrong"></div>
    <div class="correct"></div>
  </div>
  <button class="again submit">Try Again!</button>
</div>
`;

const template_revision = document.createElement("template");
template_revision.innerHTML = `
<div class="${REVISION} main hide">
  <div class="meta">
      <h1 class="name"></h1>
  </div>
  <div class="main-container">
    <p class="question"></p>
    <div class="feedbacks"></div>
    <div class="options answers"></div>
    <div class="explanation"></div>
  </div>
  <button class="back submit">Back to results</button>
</div>
`;


class JSONQuiz extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.appendChild(template_styles.content.cloneNode(true))
  }
  
  sortQuestions(questions) {
      return questions.sort(function(a, b) {
        if (a.id < b.id) return -1;
        if (a.id > b.id) return 1;
        return 0;
      });
    }

  hideContent() {
    this.shadowRoot.querySelector(".main").classList.add("hide");
  }

  showContent() {
    this.shadowRoot.querySelector(".main").classList.remove("hide");
  }

  addNode(node) {
    this.shadowRoot.appendChild(node);
    this.shadowRoot.querySelector(".main").id = `quiz-${this.data_quiz.id}`;
    this.showContent();
  }

  isAnswered(question_id) {
    return question_id in this.answered.correct
          || question_id in this.answered.wrong
          || question_id in this.answered.skipped;
  }

  removeNode(node) {
    this.hideContent();
    this.shadowRoot.removeChild(node);
  }

  swapChild(nodePrev, nodeNew) {
    this.removeNode(nodePrev);
    this.addNode(nodeNew);
  }

  createAnswers(data_question, answ_sol=[]) {
    var answers_html = ``;
      for (const ans_letter in data_question.answers) {
        let ans_text = data_question.answers[ans_letter];
        let ans_html = ANSWER_TEMPLATE.replace(/{ANS_OPT}/, ans_letter);

        if ( data_question.assessment_type === "multi-select" ) {
          ans_html = ans_html.replace(`type="radio"`, `type="checkbox"`);
        }

        ans_html = ans_html.replace(/{ANS_TEXT}/, ans_text);
        if ( answ_sol.length !== 0 ) {
          let ans_outcome = "";
          if ( answ_sol.includes(ans_letter) ) {
            ans_outcome = data_question.correct_response.includes(ans_letter) ? "correct" : "wrong";
          }
          if ( data_question.correct_response.includes(ans_letter) ) {
            ans_outcome = "correct";
          }
          if ( ans_outcome !== "" ) {
            ans_html = ans_html.replace(/<label>/, `<label class="${ans_outcome}">`);
          }

        }
        answers_html += ans_html;
      }
    return answers_html;
  }

  createFeedback(feedbacks, $mainNode=undefined) {
    let $_main = $mainNode || this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.main`);
    feedbacks.forEach((elem) => {
      let feedback_type = elem.type;
      let feedback_text = elem.text;
      let $feed = document.createElement("div");
      $feed.classList.add("feedback");
      $feed.innerText = feedback_text;
      for ( const feedback_style in FEEDBACK_STYLES[feedback_type] ) {
        $feed.style[feedback_style] = FEEDBACK_STYLES[feedback_type][feedback_style];
      }
      $_main.querySelector(".feedbacks").appendChild($feed);
    });
  }

  removeFeedback() {
    let $_main = this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.main`);
    if ( $_main ) {
      $_main.querySelectorAll(".feedback").forEach(($feed) => {
        $feed.classList.add("hide-feedback");
//        setTimeout(function() {
          $_main.querySelector(".feedbacks").removeChild($feed);
//        }, 500);
      });
    }
  }

  createQuiz(prevChildClass=undefined) {
    // Inicializar estado variables componente
    this.answered_count = {
      "correct": 0,
      "wrong": 0,
      "skipped": 0
    }
    this.answered = {
      "correct": [],
      "wrong": [],
      "skipped": []
    }

    this.question_sections = {
      "Without Section": {
        correct_answers: 0,
        wrong_answers: 0,
        skipped_questions: 0
      }
    };
    // section_name: {
    //  correct_answers: 3,
    //  wrong_answers: 4
    //  skipped_questions: 10
    // }

    this.actual_question = 0;
    let data_questions = this.data_quiz["questions"];
    data_questions = this.sortQuestions(data_questions);
    this.total_q = data_questions.length;

    // Generating html for answers
    var $quiz = template_quiz.content.cloneNode(true);

    $quiz.id = `quiz-${this.data_quiz.id}`;
    $quiz.querySelector(".meta .name").innerText = this.data_quiz["title"];
    this.createQuestion($quiz, data_questions[this.actual_question]);

    // Button Listeners
    const verifyAnswer = (e) => {
      let $_quiz = this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.quiz.main`);
      let data_question = data_questions[this.actual_question];
      let ques_id = data_questions[this.actual_question].id;

      // Posibilidad de multiples opciones
      const answer_elements = Array.from($_quiz.querySelectorAll("input[name=answer]:checked")).map((elem) => elem.value);
      if ( answer_elements.length !== 0 ) {
        let feedbacks = answer_elements.map((elem) => {
          return {
            "text": data_question.feedbacks[elem],
            "type": data_question.correct_response.includes(elem) ? "correct":"wrong"
          }
        });
        let are_correct = answer_elements.every(
          ans_val => data_question.correct_response.includes(ans_val)
        );
        let correct_ans = answer_elements.filter(elem => data_question.correct_response.includes(elem));
        let wrong_ans = answer_elements.filter(elem => !data_question.correct_response.includes(elem));

        if ( data_question.section !== "" && data_question.section !== undefined ) {
          this.question_sections[data_question.section].correct_answers += correct_ans.length;
          this.question_sections[data_questions[this.actual_question].section].wrong_answers += wrong_ans.length;
        }
        else {
          this.question_sections["Without Section"].correct_answers += correct_ans.length;
          this.question_sections["Without Section"].wrong_answers += wrong_ans.length;
        }

        if ( are_correct ) {
          if ( !this.isAnswered(ques_id) ) {
            this.answered_count.correct++;
            this.answered.correct[ques_id] = {
              "options": answer_elements,
              "question_number": this.actual_question,
              "question": data_question
            }
          }
          this.createFeedback(feedbacks);
        }
        else {
          if ( !this.isAnswered(ques_id) ) {
            this.answered_count.wrong++;
            this.answered.wrong[ques_id] = {
              "options": answer_elements,
              "question_number": this.actual_question,
              "question": data_questions[this.actual_question]
            }

          }

          this.createFeedback(feedbacks);
        }

        // Bloqueamos la pregunta
        // $_quiz.querySelectorAll(
        //   `.answers input:not(:checked)`
        // ).forEach((elem) => elem.disabled=true);
        $_quiz.querySelectorAll(
          `.answers input:checked`
        ).forEach((elem) => elem.disabled=true);
      }

    }
    $quiz.querySelector("button.verify").addEventListener("click", verifyAnswer);
    $quiz.querySelector("button.skip").addEventListener("click", (e) => {
      let $_quiz = this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.quiz.main`);
      verifyAnswer(e);
      let ques_id = data_questions[this.actual_question].id
      if (!this.isAnswered(ques_id)) {
        this.answered_count.skipped++;
        this.answered.skipped[ques_id] = {
          "options": [],
          "question_number": this.actual_question,
          "question": data_questions[this.actual_question]
        }
        if ( data_questions[this.actual_question].section !== "" && data_questions[this.actual_question].section !== undefined ) {
          this.question_sections[data_questions[this.actual_question].section].skipped_questions++
        }
        else {
          this.question_sections["Without Section"].skipped_questions++;
        }
      }

      if(this.actual_question < this.total_q-1){
        this.actual_question++;
        this.createQuestion(this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.${QUIZ}`), data_questions[this.actual_question]);
      }
      else {
        this.createQuizResults(QUIZ);
      }
    });

    // Se agrega el nodo al componente
    if ( prevChildClass ) {
      this.swapChild(this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.${prevChildClass}`), $quiz);
    }
    else {
      this.addNode($quiz);
    }
  }

  createWrongQuiz() {
      // Generating html for answers
      var $wrong_quiz = template_wrong_quiz.content.cloneNode(true);

      $wrong_quiz.id = `quiz-${this.data_quiz.id}`;
      $wrong_quiz.querySelector(".meta .name").innerText = this.data_quiz.title;

      $wrong_quiz.querySelector(".wrong-reason").innerText = this.data_quiz.wrong_reason || "Unknown";

      this.addNode($wrong_quiz);
    }

  createQuestion($parentNode, data_question) {
    // Se quita el feedback
    this.removeFeedback();

    const question_text = data_question.question;
    $parentNode.querySelector(".question").innerText = `Q${this.actual_question+1}: ${question_text}`;

    const answers_html = this.createAnswers(data_question);
    $parentNode.querySelector(".options").innerHTML = answers_html;

    if ( this.question_sections[data_question.section] === undefined &&
      data_question.section !== "" &&
      data_question.section !== undefined
    ) {
      this.question_sections[data_question.section] = {
        correct_answers: 0,
        wrong_answers: 0,
        skipped_questions: 0
      }
    }
  }

  createQuizResults(actualMainChildClass) {
    let $results = template_results.content.cloneNode(true);
    $results.id = `quiz-${this.data_quiz.id}`;
    $results.querySelector(".name").innerText = this.data_quiz.title;
    $results.querySelector(".scoreboard").innerText = `You got ${this.answered_count.correct} out of ${this.total_q}.`;
    if ( this.answered_count.skipped > 0 ){
      $results.querySelector(".scoreboard").innerText += ` You have skipped ${this.answered_count.skipped} questions.`;
    }

    let $sections = $results.querySelector(".overall-sections");

    for (let sect in this.question_sections) {
      let total_questions = this.question_sections[sect].correct_answers + this.question_sections[sect].wrong_answers + this.question_sections[sect].skipped_questions;

      if ( total_questions > 0 ) {
        let correct_percent = this.question_sections[sect].correct_answers/total_questions * 100;
        let wrong_percent = this.question_sections[sect].wrong_answers/total_questions * 100;
        let skipped_percent = this.question_sections[sect].skipped_questions/total_questions * 100;
        let $sect = document.createElement("div");
        $sect.classList.add("section");
        $sect.innerHTML = SECTION_TEMPLATE;
        $sect.innerHTML += SECTION_PROGRESS_TEMPLATE;

        if ( correct_percent > 0 ) {
          $sect.querySelector(".progress.sect-correct").style.width = `calc(${correct_percent}% - 2px)`;
          $sect.querySelector(".progress.sect-correct label").innerText = `${parseInt(correct_percent*1000)/1000} %`;
        } else{
          $sect.querySelector(".progress.sect-correct").remove();
        }

        if ( wrong_percent > 0 ) {
          $sect.querySelector(".progress.sect-wrong").style.width = `calc(${wrong_percent}% - 2px)`;
          $sect.querySelector(".progress.sect-wrong label").innerText = `${parseInt(wrong_percent*1000)/1000} %`;
        } else{
          $sect.querySelector(".progress.sect-wrong").remove();
        }

        if ( skipped_percent > 0 ) {
          $sect.querySelector(".progress.sect-skipped").style.width = `calc(${skipped_percent}% - 2px)`;
          $sect.querySelector(".progress.sect-skipped label").innerText = `${parseInt(skipped_percent*1000)/1000} %`;
        } else{
         $sect.querySelector(".progress.sect-skipped").remove();
       }

        $sect.querySelector(".sect-name").innerText = sect;
        $sections.appendChild($sect);
      }
    }

    for (const q_outcome in this.answered) {
      let header_res = ANSWERED_MSG[q_outcome].replace(/{}/, this.answered_count[q_outcome]);
      $results.querySelector(`.${q_outcome}`).innerHTML += `<h3>${header_res}</h3>`;
      for (const question_id in this.answered[q_outcome]) {
        let data_question = this.answered[q_outcome][question_id].question;
        let question_number = this.answered[q_outcome][question_id].question_number;
        let answer_options = this.answered[q_outcome][question_id].options;

        let $q_result = document.createElement("label");
        $q_result.classList.add("question-revision");
        $q_result.id = question_id;
        $q_result.innerText = data_question.question;
        $q_result.addEventListener("click", (e) => {
          this.createQuestionRevision(question_number, q_outcome, answer_options, data_question);
        });
        $results.querySelector(`.${q_outcome}`).appendChild($q_result);
      }
    }

    $results.querySelector("button.again").addEventListener("click", (e) => {
      // Se genera otra vez el quiz entero desde cero
      this.createQuiz(RESULTS);
    });

    this.swapChild(this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.${actualMainChildClass}`), $results);
  }

  createQuestionRevision(question_number, question_outcome, answer_options, data_question) {
    var $revision = template_revision.content.cloneNode(true);
    $revision.id = `quiz-${this.data_quiz.id}`;
    // Se agrega el feedback
    let orig_answer_options = answer_options;
    let ans_skipped = false;
    if ( answer_options.length === 0 ) {
      ans_skipped = true;
      answer_options = data_question.correct_response;
    }

    let feedbacks = answer_options.map((ans_elem) => {
      return {
        "text": data_question.feedbacks[ans_elem],
        "type": ans_skipped ? "skipped" : data_question.correct_response.includes(ans_elem) ? "correct":"wrong"
      }
    });

    this.createFeedback(feedbacks, $revision);

    $revision.querySelector(".question").innerText =`Q${question_number+1}: ` + data_question.question;

    const answers_html = this.createAnswers(data_question, answer_options);
    $revision.querySelector(".options").innerHTML = answers_html;
    if ( !ans_skipped ) {
      orig_answer_options.forEach((ans_elem) => {
        $revision.querySelector(`.options input[value=${ans_elem}]`).checked = true;
      });
    }

    $revision.querySelectorAll(
      `.answers input:not(:checked)`
    ).forEach((elem) => elem.disabled=true);

    if ( data_question.explanationHTML ) {
      $revision.querySelector(".explanation").innerHTML = data_question.explanationHTML;
    }
    else {
      $revision.querySelector(".explanation").removeChild();
    }

    $revision.querySelector("button.back").addEventListener("click", (e) => {
      this.createQuizResults(REVISION);
    });

    this.swapChild(this.shadowRoot.querySelector(`#quiz-${this.data_quiz.id}.${RESULTS}`), $revision);
  }

  connectedCallback() {
    fetch(this.getAttribute("json-file"))
      .then((res) => res.json())
      .then((data_quiz) => {
        this.data_quiz = data_quiz;
        if ( this.data_quiz.validated !== undefined ) {
          this.createQuiz();
        }
        else {
          this.createWrongQuiz();
        }

    });
  }
  disconnectedCallback() {
    this.shadowRoot.querySelector("button").removeEventListener();
  }
}
window.customElements.define("json-quiz", JSONQuiz);
