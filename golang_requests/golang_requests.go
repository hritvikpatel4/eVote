package main

import (
	"bytes"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math/big"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"sync/atomic"
	"time"
)

var (
	success uint64
	fail    uint64
)

func exec_python_code() []string {
	python_script := exec.Command("python3", "write_election_data.py")

	python_script_output, err := python_script.Output()
	if err != nil {
		panic(err)
	} else {
		fmt.Println("\n\tpython3 write_election_data.py", string(python_script_output))
	}

	election_data, err := os.ReadFile("./election_data.txt")
	if err != nil {
		log.Fatalf("Failed reading file.\n%s", err)
	}

	election_data_arr := strings.Split(string(election_data), "\n")

	return election_data_arr
}

func send_request(workerid int, batch_ids <-chan int, responses chan<- string, election_data_arr []string) {
	vote_endpoint := "http://34.117.144.244:80/castVote"

	for batch_id := range batch_ids {
		data := make(map[string]int)

		data["level_number"] = 0
		data["cluster_id"] = 1
		data["batch_id"] = batch_id

		for i := 0; i < len(election_data_arr); i++ {
			data[election_data_arr[i]] = 0
		}

		arr_index, err := rand.Int(rand.Reader, big.NewInt(int64(len(election_data_arr))))
		if err != nil {
			panic(err)
		}

		data[election_data_arr[arr_index.Int64()]] = 1

		json_data, err := json.Marshal(data)
		if err != nil {
			log.Fatal(err)
		}

		req, err := http.NewRequest(http.MethodPost, vote_endpoint, bytes.NewBuffer(json_data))
		if err != nil {
			panic(err)
		}

		req.Header.Set("Content-Type", "application/json")
		req.Close = true

		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			log.Fatal(err)
		}

		resp_body, _ := io.ReadAll(resp.Body)

		if resp.StatusCode == http.StatusOK {
			atomic.AddUint64(&success, 1)
			responses <- fmt.Sprintf("\033[32m[Success %d] worker %d batch_id %d | Body = %s", resp.StatusCode, workerid, batch_id, string(resp_body))
			// log.Printf("Sent request %d", batch_id)
		} else {
			atomic.AddUint64(&fail, 1)
			responses <- fmt.Sprintf("\033[31m[Failure %d] worker %d batch_id %d | Body %s", resp.StatusCode, workerid, batch_id, string(resp_body))
			// log.Fatalf("Error sending request %d", batch_id)
		}

		resp.Body.Close()
	}
}

func main() {
	election_data_arr := exec_python_code()

	start := time.Now()

	start_id := 1
	number_of_requests := 1_000

	batch_ids := make(chan int, number_of_requests)
	responses := make(chan string, number_of_requests)

	for num := 1; num <= 12; num++ {
		go send_request(num, batch_ids, responses, election_data_arr)
	}

	for num := start_id; num < start_id+number_of_requests; num++ {
		batch_ids <- num
	}
	close(batch_ids)

	for num := start_id; num < start_id+number_of_requests; num++ {
		fmt.Println(<-responses)
	}
	close(responses)

	fmt.Println(time.Since(start).Seconds())
	fmt.Printf("Successful requests = %d | %f rps\n", success, float64(float64(success)/float64(time.Since(start).Seconds())))
	fmt.Printf("Failed requests = %d | %f rps\n", fail, float64(float64(fail)/float64(time.Since(start).Seconds())))
	fmt.Printf("Total requests = %d | %f rps\n", success+fail, float64(float64(success+fail)/float64(time.Since(start).Seconds())))
}
