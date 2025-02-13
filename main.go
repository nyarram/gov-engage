package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/url"
	"os"
	"os/exec"

	"github.com/gin-gonic/gin"
	"github.com/go-resty/resty/v2"
	_ "github.com/lib/pq"
)

// Database connection
var db *sql.DB

type LocationData struct {
	Country   string  `json:"country"`
	Region    string  `json:"region"`
	City      string  `json:"city"`
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
}

type CivicResponse struct {
	Offices []struct {
		Name       string `json:"name"`
		DivisionID string `json:"divisionId"`
		Officials  []int  `json:"officialIndices"`
	} `json:"offices"`
	Officials []struct {
		Name  string `json:"name"`
		Party string `json:"party"`
	} `json:"officials"`
}

var sampleIPs = map[string]LocationData{
	"192.119.0.1": {Country: "United States", Region: "California", City: "San Francisco", Latitude: 37.7749, Longitude: -122.4194},
	"65.132.0.2":  {Country: "United States", Region: "Illinois", City: "Chicago", Latitude: 41.8781, Longitude: -87.6298},
	"104.15.0.3":  {Country: "United States", Region: "New York", City: "New York", Latitude: 40.7128, Longitude: -74.0060},
}

func connectDB() {
	var err error
	connStr := "postgres://nikhilyarram@localhost/political_engagement?sslmode=disable"
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal("Error connecting to the database:", err)
	}
}

func getHardcodedLocation(ip string) (*LocationData, error) {
	location, exists := sampleIPs[ip]
	if !exists {
		return nil, fmt.Errorf("IP not found in sample data")
	}
	return &location, nil
}

func getGovernmentData(address string) (*CivicResponse, error) {
	client := resty.New()
	apiKey := os.Getenv("GOOGLE_CIVIC_API_KEY")

	encodedAddress := url.QueryEscape(address)
	url := fmt.Sprintf("https://www.googleapis.com/civicinfo/v2/representatives?address=%s&key=%s", encodedAddress, apiKey)

	resp, err := client.R().SetResult(&CivicResponse{}).Get(url)
	if err != nil {
		return nil, err
	}

	return resp.Result().(*CivicResponse), nil
}

func storeUserLocation(ip string, location *LocationData) error {
	_, err := db.Exec(`
		INSERT INTO users (ip, country, region, city, latitude, longitude)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (ip) DO NOTHING;`,
		ip, location.Country, location.Region, location.City, location.Latitude, location.Longitude)
	return err
}

func storeOfficials(ip string, officials []gin.H) error {
	for _, official := range officials {
		var count int
		err := db.QueryRow(`
			SELECT COUNT(*) FROM officials WHERE name = $1 AND position = $2 AND user_ip = $3`,
			official["name"], official["position"], ip).Scan(&count)

		if err != nil {
			log.Println("Error checking for duplicate official:", err)
			continue
		}

		// If count == 0, insert the new record
		if count == 0 {
			_, err := db.Exec(`
				INSERT INTO officials (position, name, party, user_ip)
				VALUES ($1, $2, $3, $4);`,
				official["position"], official["name"], official["party"], ip)

			if err != nil {
				log.Println("Error inserting official:", err)
			}
		}
	}
	return nil
}

func trackPromiseProgress(politician string) (string, error) {
	cmd := exec.Command("python3", "track_progress.py", politician)
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return string(output), nil
}

func main() {
	connectDB()
	defer db.Close()

	r := gin.Default()

	r.GET("/", func(c *gin.Context) {
		userIP := c.Query("ip")
		if userIP == "" {
			userIP = "65.132.0.2"
		}

		location, err := getHardcodedLocation(userIP)
		if err != nil {
			c.JSON(404, gin.H{"error": "IP not found in sample data"})
			return
		}

		storeUserLocation(userIP, location)

		address := fmt.Sprintf("%s, %s, %s", location.City, location.Region, location.Country)
		govData, err := getGovernmentData(address)
		if err != nil {
			c.JSON(500, gin.H{"error": "Unable to fetch government data"})
			return
		}

		var officials []gin.H
		for _, office := range govData.Offices {
			for _, index := range office.Officials {
				if index >= 0 && index < len(govData.Officials) {
					official := govData.Officials[index]
					officials = append(officials, gin.H{
						"position": office.Name,
						"name":     official.Name,
						"party":    official.Party,
					})
				}
			}
		}

		storeOfficials(userIP, officials)

		c.JSON(200, gin.H{
			"ip":        userIP,
			"location":  location,
			"officials": officials,
		})
	})

	r.Run(":8080")
}
