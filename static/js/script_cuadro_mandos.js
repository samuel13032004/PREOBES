
        // Inicializar gráficos cuando se carga la página
        document.addEventListener('DOMContentLoaded', function() {
            // Gráfico de impacto de factores
            const ctxImpact = document.getElementById('factorImpactChart').getContext('2d');
            const impactChart = new Chart(ctxImpact, {
                type: 'bar',
                data: {
                    labels: ['Uso de Tecnología', 'Actividad Física', 'Consumo de Agua', 'Consumo de Vegetales', 'Nº comidas principales'],
                    datasets: [{
                        label: 'Impacto en Riesgo de Obesidad (%)',
                        data: [13.7, 12.8, 12.4, 20.2, 13.5],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#e0e0e0'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#e0e0e0'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: '#e0e0e0'
                            }
                        }
                    }
                }
            });

            // Gráfico de distribución de riesgo
            const ctxDistribution = document.getElementById('riskDistributionChart').getContext('2d');
            const distributionChart = new Chart(ctxDistribution, {
                type: 'doughnut',
                data: {
                    labels: ['Factores Dietéticos', 'Estilo de Vida', 'Genética', "Factores de Consumo de Sustancias", "Otros"],
                    datasets: [{
                        data: [38.2, 21.3, 22.3, 5.3, 12.9],
                        backgroundColor: [
                            '#4e73df',
                            '#1cc88a',
                            '#36b9cc',
                            '#f6c23e',
                            '#e74a3b'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: '#e0e0e0'
                            }
                        }
                    }
                }
            });
        });

// Grafo de relaciones
        document.querySelectorAll('.tab').forEach(function(tab) {
                tab.addEventListener('click', function() {
                    if (this.textContent.includes('Análisis de Relaciones')) {
                        setTimeout(cargarGrafoRelaciones, 100);
                    }
                });
            });


        function cargarGrafoRelaciones() {
            // Limpiar el contenedor por si se ha cargado previamente
            document.getElementById('grafoRelaciones').innerHTML = '';

            // Datos completos para el grafo
            const nodos = [
                { id: "Weight", type: "numeric", description: "Peso del individuo en kg" },
                { id: "Height", type: "numeric", description: "Altura del individuo en cm" },
                { id: "Age", type: "numeric", description: "Edad del individuo en años" },
                { id: "Gender", type: "categorical", description: "Género del individuo (Masculino/Femenino)" },
                { id: "family_history", type: "categorical", description: "Historial familiar de obesidad (Sí/No)" },
                { id: "FAVC", type: "categorical", description: "Frecuencia de consumo de alimentos con alto contenido calórico" },
                { id: "FCVC", type: "numeric", description: "Frecuencia de consumo de vegetales" },
                { id: "NCP", type: "numeric", description: "Número de comidas principales al día" },
                { id: "CAEC", type: "categorical", description: "Consumo de alimentos entre comidas" },
                { id: "SMOKE", type: "categorical", description: "Hábito de fumar (Sí/No)" },
                { id: "CH2O", type: "numeric", description: "Consumo de agua diario en litros" },
                { id: "SCC", type: "categorical", description: "Control del consumo de calorías (Sí/No)" },
                { id: "FAF", type: "numeric", description: "Frecuencia de actividad física" },
                { id: "TUE", type: "numeric", description: "Tiempo de uso de dispositivos tecnológicos en horas" },
                { id: "CALC", type: "categorical", description: "Consumo de alcohol" },
                { id: "MTRANS", type: "categorical", description: "Medio de transporte habitual" },
                { id: "obesity_level", type: "categorical", description: "Nivel de obesidad (Insuficiente/Normal/Sobrepeso/Obesidad)" },
                { id: "IMC", type: "numeric", description: "Índice de Masa Corporal (kg/m²)" }
            ];

            const enlaces = [
                { source: "Weight", target: "Height", type: "positive" ,strength: 0.5},
                { source: "Age", target: "Weight", type: "positive"},
                { source: "Age", target: "Gender", type: "anova"},
                { source: "Gender", target: "Height", type: "anova",strength: 0.4 },
                { source: "IMC", target: "family_history", type: "anova" },
                { source: "Weight", target: "IMC", type: "positive", strength: 0.9 },
                { source: "IMC", target: "obesity_level", type: "anova", strength: 1.1 },
                { source: "IMC", target: "Gender", type: "anova" },
                { source: "FCVC", target: "obesity_level", type: "anova" },
                { source: "FCVC", target: "IMC", type: "positive" },
                { source: "FCVC", target: "Weight", type: "positive" },
                { source: "family_history", target: "FAVC", type: "chi2" },
                { source: "family_history", target: "obesity_level", type: "chi2",strength: 0.6 },
                { source: "FAVC", target: "obesity_level", type: "chi2", strength: 0.3 },
                { source: "CAEC", target: "obesity_level", type: "chi2" , strength: 0.3},
                { source: "SCC", target: "obesity_level", type: "chi2" },
                { source: "obesity_level", target: "Gender", type: "chi2",strength: 0.7 },
                { source: "obesity_level", target: "Weight", type: "anova",strength: 0.9 },
                { source: "Height", target: "FAF", type: "positive" },
                { source: "Height", target: "CH2O", type: "positive" },
                { source: "Weight", target: "CH2O", type: "positive" },
                { source: "Height", target: "NCP", type: "positive" },
                { source: "Age", target: "MTRANS", type: "anova" },
                { source: "FAVC", target: "MTRANS", type: "chi2" },
                { source: "CALC", target: "obesity_level", type: "chi2" },
                { source: "TUE", target: "Age", type: "negative" },

            ];

            // Configuración del grafo
            const width = document.getElementById('grafoRelaciones').clientWidth;
            const height = 600;

            // Crear el SVG
            const svg = d3.select("#grafoRelaciones")
                .append("svg")
                .attr("width", width)
                .attr("height", height)
                .attr("viewBox", [0, 0, width, height])
                .attr("style", "max-width: 100%; height: auto;");

            const tooltip = d3.select("body").append("div")
                .attr("class", "tooltip")
                .style("opacity", 0)
                .style("position", "absolute")
                .style("background-color", "rgba(0, 0, 0, 0.8)")
                .style("color", "white")
                .style("padding", "10px")
                .style("border-radius", "5px")
                .style("pointer-events", "none")
                .style("z-index", "10")
                .style("font-size", "14px")
                .style("max-width", "250px");
            // Crear la simulación de fuerza
            const simulation = d3.forceSimulation(nodos)
                .force("link", d3.forceLink(enlaces).id(d => d.id).distance(120))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(40));

            // Definir colores para los tipos de relaciones
            const colorRelacion = {
                "positive": "#4CAF50",
                "negative": "#F44336",
                "anova": "#FF9800",
                "chi2": "#9C27B0"
            };
            const lineWidth = d => {
                // Si la fortaleza no está definida, usa 2 como valor predeterminado
                if (!d.strength) return 2;
                // Mapea la fortaleza (normalmente entre 0 y 1) a valores entre 1 y 5
                return 1 + (d.strength * 4);
            };
            // Crear las líneas para los enlaces
            const link = svg.append("g")
                .selectAll("line")
                .data(enlaces)
                .enter()
                .append("line")
                .attr("stroke", d => colorRelacion[d.type])
                .attr("stroke-width", lineWidth);

            // Crear los círculos para los nodos
            const node = svg.append("g")
                .selectAll("circle")
                .data(nodos)
                .enter()
                .append("circle")
                .attr("r", d => d.id === "obesity_level" ? 20 : 15)
                .attr("fill", d => d.type === "numeric" ? "#90CAF9" : "#A5D6A7")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended))
                    .on("mouseover", function(event, d) {
                    tooltip.transition()
                        .duration(200)
                        .style("opacity", .9);
                    tooltip.html(`<strong>${d.id}</strong><br>${d.description}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                    })
                    .on("mouseout", function() {
                        tooltip.transition()
                            .duration(500)
                            .style("opacity", 0);
                    });
            // Añadir etiquetas a los nodos
            const text = svg.append("g")
                .selectAll("text")
                .data(nodos)
                .enter()
                .append("text")
                .text(d => d.id)
                .attr("font-size", d => d.id === "obesity_level" ? 12 : 10)
                .attr("text-anchor", "middle")
                .attr("dy", 3)
                .attr("fill", "#fff")
                .attr("font-size", d => {
                    // Ajustar el tamaño de la fuente según la longitud del texto
                    // Palabras especiales que queremos asegurar que se ven bien
                    const specialWords = ["Weight", "Height", "MTRANS", "Gender","SMOKE"];

                    // Tamaño fijo para palabras especiales
                    if (specialWords.includes(d.id)) {
                        return 8; // Tamaño fijo para estas palabras
                    }

                    // Para el resto, usar la lógica de ajuste automático
                    const textLength = d.id.length;
                    return Math.max(8, Math.min(12, 18 - textLength));
                })
                .text(d => {
                    // Acortar el texto si es muy largo
                    if (d.id.length > 10) {
                        return d.id.slice(0, 7) + "...";
                    }
                    return d.id;
                });

            // Crear una leyenda
            const legend = svg.append("g")
                .attr("transform", "translate(20, 20)");

            // Añadir elementos de la leyenda
            const legendData = [
                { label: "Correlación Positiva", color: "#4CAF50", type: "line" },
                { label: "Correlación Negativa", color: "#F44336", type: "line" },
                { label: "ANOVA", color: "#FF9800", type: "line" },
                { label: "Chi²", color: "#9C27B0", type: "line" },
                { label: "Var. Numérica", color: "#90CAF9", type: "circle" },
                { label: "Var. Categórica", color: "#A5D6A7", type: "circle" }
            ];

            legendData.forEach((item, i) => {
                const legendRow = legend.append("g")
                    .attr("transform", `translate(0, ${i * 20})`);

                if (item.type === "line") {
                    legendRow.append("line")
                        .attr("x1", 0)
                        .attr("y1", 10)
                        .attr("x2", 30)
                        .attr("y2", 10)
                        .attr("stroke", item.color)
                        .attr("stroke-width", 2);
                } else {
                    legendRow.append("circle")
                        .attr("cx", 15)
                        .attr("cy", 10)
                        .attr("r", 7)
                        .attr("fill", item.color);
                }

                legendRow.append("text")
                    .attr("x", 40)
                    .attr("y", 10)
                    .attr("dy", "0.35em")
                    .text(item.label)
                    .attr("fill", "#e0e0e0");
            });

            // Actualizar la posición en cada tick
            simulation.on("tick", () => {
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node
                    .attr("cx", d => d.x = Math.max(20, Math.min(width - 20, d.x)))
                    .attr("cy", d => d.y = Math.max(20, Math.min(height - 20, d.y)));

                text
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
            });

            // Agregar tooltips
            node.append("title")
                .text(d => d.id);

            // Funciones para el arrastre
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }

            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
        }

 document.getElementById('variableForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const variableForm = document.getElementById("variableForm");
    variableForm.removeEventListener("submit", handleVariableSubmit);
    variableForm.addEventListener("submit", handleVariableSubmit);

    function handleVariableSubmit(event) {
        event.preventDefault();
        const variable = document.getElementById("variable").value;

        fetch(`/evolucion-data?variable=${variable}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }

                const labels = data.report_numbers;
                const variableValues = data.variable_values;
                const variableLabel = data.variable_name;
                const isCategorical = data.is_categorical;
                const categories = data.categories;

                // Destruir la gráfica existente si existe
                const existingChart = Chart.getChart("evolucionChart");
                if (existingChart) {
                    existingChart.destroy();
                }

                const ctx = document.getElementById('evolucionChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: variableLabel,
                            data: variableValues,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 2,
                            tension: 0.1,
                            pointRadius: 4,  // 🔹 Puntos más pequeños
                            pointHoverRadius: 6 // 🔹 Aumenta el tamaño al pasar el ratón
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: `Evolución de ${variableLabel}`
                            },
                            tooltip: { // 🔹 Tooltip mejorado
                                enabled: true,
                                animation: false, // 🔹 Aparece al instante
                                callbacks: {
                                    label: function(context) {
                                        const reportNumber = labels[context.dataIndex];
                                        let value = context.raw;

                                        if (isCategorical) {
                                            value = categories[value] || "Desconocido";
                                        }

                                        return [`Nº Informe: ${reportNumber}`, `${variableLabel}: ${value}`];
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Número de Informe'
                                }
                            },
                            y: isCategorical ? {
                                title: {
                                    display: true,
                                    text: variableLabel
                                },
                                min: 0,
                                max: categories.length - 1,
                                ticks: {
                                    stepSize: 1,
                                    callback: function(value) {
                                        return categories[value] || "";
                                    }
                                }
                            } : {
                                title: {
                                    display: true,
                                    text: variableLabel
                                },
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ocurrió un error al obtener los datos');
            });
    }
});
//Matriz de correlacion


        const correlationData = [
                [1.0, -0.02577, 0.20345, 0.24507, 0.01702, -0.04395, -0.04558, -0.14508, -0.29661],
                [-0.02577, 1.0, 0.46226, 0.13016, -0.03858, 0.24339, 0.21347, 0.29535, 0.05158],
                [0.20345, 0.46226, 1.0, 0.93456, 0.21627, 0.10741, 0.20054, -0.05136, -0.07157],
                [0.24507, 0.13016, 0.93456, 1.0, 0.26396, 0.03992, 0.14403, -0.17788, -0.09959],
                [0.01702, -0.03858, 0.21627, 0.26396, 1.0, 0.04205, 0.06840, 0.01994, -0.10122],
                [-0.04395, 0.24339, 0.10741, 0.03992, 0.04205, 1.0, 0.05694, 0.12952, 0.03640],
                [-0.04558, 0.21347, 0.20054, 0.14403, 0.06840, 0.05694, 1.0, 0.16718, 0.01192],
                [-0.14508, 0.29535, -0.05136, -0.17788, 0.01994, 0.12952, 0.16718, 1.0, 0.05859],
                [-0.29661, 0.05158, -0.07157, -0.09959, -0.10122, 0.03640, 0.01192, 0.05859, 1.0]
            ];

            const headers = ['Age', 'Height', 'Weight', 'IMC', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE'];

            const matrix = document.querySelector('.correlation-matrix');

            // Color mapping function
            function getColor(value) {
                // Absolute value for consistent coloring
                const absValue = Math.abs(value);

                // Diagonal case
                if (absValue === 1) {
                    return 'rgb(76, 175, 80)'; // Solid green
                }

                // Positive correlations (green spectrum)
                if (value > 0) {
                    // More intense green for stronger positive correlations
                    const intensity = Math.min(255, Math.floor(absValue * 255));
                    return `rgb(${255 - intensity}, 255, ${255 - intensity})`;
                }

                // Negative correlations (red spectrum)
                if (value < 0) {
                    // More intense red for stronger negative correlations
                    const intensity = Math.min(255, Math.floor(absValue * 255));
                    return `rgb(255, ${255 - intensity}, ${255 - intensity})`;
                }

                // Neutral (very weak) correlations
                return 'rgb(245, 245, 245)';
            }

            // Add empty cell for top-left corner
            const emptyCell = document.createElement('div');
            emptyCell.classList.add('matrix-cell');
            matrix.appendChild(emptyCell);

            // Add horizontal headers
            headers.forEach(header => {
                const headerCell = document.createElement('div');
                headerCell.textContent = header;
                headerCell.classList.add('matrix-cell', 'header');
                matrix.appendChild(headerCell);
            });

            // Create matrix cells
            correlationData.forEach((row, rowIndex) => {
                // Add vertical header
                const verticalHeader = document.createElement('div');
                verticalHeader.textContent = headers[rowIndex];
                verticalHeader.classList.add('matrix-cell', 'header');
                matrix.appendChild(verticalHeader);

                row.forEach((value, colIndex) => {
                    const cell = document.createElement('div');
                    cell.textContent = value.toFixed(3);
                    cell.classList.add('matrix-cell');

                    // Set background color based on correlation value
                    cell.style.backgroundColor = getColor(value);

                    // Ensure readability of text
                    cell.style.color = 'black';

                    // Diagonal cells styling
                    if (rowIndex === colIndex) {
                        cell.classList.add('diagonal');
                    }

                    matrix.appendChild(cell);
                });
            });


            // fecha de nacimiento
         document.getElementById("birthdate").addEventListener("change", function () {
            const birthdate = new Date(this.value);
            const today = new Date();
            let age = today.getFullYear() - birthdate.getFullYear();
            const monthDiff = today.getMonth() - birthdate.getMonth();
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthdate.getDate())) {
                age--;
            }
            console.log("Edad calculada:", age);
        });







         // Función para cargar los informes cuando se abra la pestaña correspondiente
function loadUserReports() {
    const reportsContainer = document.getElementById('reports-container');
    const loadingElement = document.getElementById('loading-reports');

    // Mostrar mensaje de carga
    if (loadingElement) loadingElement.style.display = 'block';
    if (reportsContainer) reportsContainer.innerHTML = '';

    // Realizar la petición AJAX para obtener los informes
    fetch('/api/user_reports')
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar informes');
            }
            return response.json();
        })
        .then(data => {
            // Ocultar mensaje de carga
            if (loadingElement) loadingElement.style.display = 'none';

            // Verificar si hay informes
            if (data.reports && data.reports.length > 0) {
                // Crear lista de informes
                const reportsList = document.createElement('ul');
                reportsList.className = 'reports-list';

                data.reports.forEach(report => {
                    const reportItem = document.createElement('li');
                    reportItem.innerHTML = `
                        📄 Informe Nº ${report.report_number} - 
                        <a href="/static/reports/${report.filename}" target="_blank">
                            Descargar informe
                        </a>
                    `;
                    reportsList.appendChild(reportItem);
                });

                reportsContainer.appendChild(reportsList);
            } else {
                // Mostrar mensaje si no hay informes
                reportsContainer.innerHTML = '<p>No tienes informes generados aún.</p>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (loadingElement) loadingElement.style.display = 'none';
            reportsContainer.innerHTML = '<p>No se pudieron cargar los informes. Por favor, intenta nuevamente.</p>';
        });
}

// Modificar la función openTab para cargar los informes cuando se seleccione esa pestaña
function openTab(tabName) {
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    const tabs = document.getElementsByClassName('tab');
    for (let i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('active');
    }
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');

    // Si se selecciona la pestaña de informes, cargar los informes
    if (tabName === 'mis_informes') {
        loadUserReports();
    }
}

// También podemos cargar los informes cuando la página se cargue completamente
document.addEventListener('DOMContentLoaded', function() {
    // Si la pestaña activa es la de informes, cargar informes
    if (document.getElementById('mis_informes').classList.contains('active')) {
        loadUserReports();
    }
});