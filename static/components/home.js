export default {
    template: `
    <div>
        <!-- Search Box -->
        <div class="search-box">
          <input type="text" v-model="searchQuery" placeholder="Enter search query" @keyup.enter="startChat" />
          <button @click="startChat">Search</button>
        </div>
        <!-- Search History -->
        <div class="search-history" v-if="previousSearches.length">
          <h3>Previous Searches</h3>
          <ul>
            <li v-for="(search, index) in previousSearches" :key="index">
              <button @click="loadPreviousChat(search)">{{ search }}</button>
            </li>
          </ul>
        </div>
        <!-- Chat System -->
        <div v-if="chatStarted" class="chat-system">
          <div class="chat-box">
            <div class="message" v-for="message in messages" :key="message.id">
              <span :class="{'user': message.sender === 'user', 'llm': message.sender === 'llm'}">{{ message.text }}</span>
            </div>
          </div>
          <input type="text" v-model="userMessage" placeholder="Ask a question" @keyup.enter="sendMessage" />
          <button @click="sendMessage">Send</button>
        </div>
        <!-- Complete Session Button -->
        <div v-if="chatStarted" class="complete-session">
          <button @click="completeSession">Complete Session</button>
        </div>
    </div>
    
    `
    ,
    data() {
        return {
          searchQuery: '',
          userMessage: '',
          chatStarted: false,
          messages: [],
          previousSearches: [],
        };
      },
      methods: {
        async startChat() {
          if (this.searchQuery.trim()) {
            this.chatStarted = true;
            this.messages.push({ id: Date.now(), sender: 'user', text: `Search query: ${this.searchQuery}` });
            
            try {
              const response = await fetch("http://127.0.0.1:5000/search", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ search_query: this.searchQuery }),
              });
              const data = await response.json();
              this.messages.push({ id: Date.now(), sender: 'llm', text: data.message });
            } catch (error) {
              console.error("Error:", error);
            }
          }
        },
        async sendMessage() {
          if (this.userMessage.trim()) {
            this.messages.push({ id: Date.now(), sender: 'user', text: this.userMessage });
            
            try {
              const response = await fetch("http://127.0.0.1:5000/query", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ query: this.userMessage , search_query: this.searchQuery }),
                //body: JSON.stringify({ search_query: this.searchQuery })
              });
              const data = await response.json();
              this.messages.push({ id: Date.now(), sender: 'llm', text: data.response });
            } catch (error) {
              console.error("Error:", error);
            }
            this.userMessage = ''; // Clear input
          }
        },
        async completeSession() {
          //if (this.searchQuery.trim()) {
            //this.chatStarted = true;
            //this.messages.push({ id: Date.now(), sender: 'user', text: `Search query: ${this.searchQuery}` });
          try {
            const response = await fetch("http://127.0.0.1:5000/complete", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ search_query: this.searchQuery }),
            });
            const data = await response.json();
            this.messages.push({ id: Date.now(), sender: 'llm', text: data.message });
          } catch (error) {
            console.error("Error:", error);
          }
        },
        async loadPreviousChat(searchQuery) {
          this.searchQuery = searchQuery;
          this.chatStarted = true;
          this.messages = []; // Clear previous messages
    
          try {
            const response = await fetch("http://127.0.0.1:5000/load_chat", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ search_query: searchQuery }),
            });
            const data = await response.json();
            
            if (data.messages) {
              console.log(data.message);
              // Load the previous chat messages
              //data.messages.forEach((msg) => {
                //this.messages.push({ id: Date.now(), sender: msg.sender, text: msg.text });
              } else{
                console.error(data.error);
              //});
            }
          } catch (error) {
            console.error("Error:", error);
          }
        },
        async fetchSearchHistory() {
          try {
            const response = await fetch("http://127.0.0.1:5000/search_history", {
              method: "GET",
            });
            const data = await response.json();
            this.previousSearches = data.history || [];
          } catch (error) {
            console.error("Error fetching search history:", error);
          }
        },
      },
      created() {
        // Fetch previous search history when the app loads
        this.fetchSearchHistory();
      },
}

  
